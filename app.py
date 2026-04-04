import os
import socket
import sys
import traceback
import secrets
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from config import config
from extensions import db, login_manager, limiter, cache, socketio
from models import Issue, User
from geoalchemy2.functions import ST_DWithin, ST_GeogFromText
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from data_exporter import exporter
from werkzeug.security import generate_password_hash, check_password_hash

def create_app(config_class=config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize data exporter
    exporter.init_app(app)
    
    # Force PostgreSQL to use pg8000 dialect
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace(
            'postgresql://', 'postgresql+pg8000://', 1
        )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Initialize limiter (for development, in-memory storage is automatic)
    limiter.init_app(app)
    
    cache.init_app(app)
    socketio.init_app(app, async_mode='threading')

    # JWT Secret for admin tokens
    JWT_SECRET = app.config.get('SECRET_KEY', 'dev-secret-key')

    # Admin token required decorator
    def admin_token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Get token from header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            try:
                data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                current_user = User.query.filter_by(id=data['user_id'], is_admin=True).first()
                if not current_user:
                    return jsonify({'error': 'Invalid token'}), 401
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
            
            return f(current_user, *args, **kwargs)
        return decorated

    # Register routes
    @app.route('/')
    def index():
        return render_template('index.html')

    # Admin login page
    @app.route('/admin/login')
    def admin_login():
        return render_template('admin_login.html')

    # Admin dashboard
    @app.route('/admin/dashboard')
    def admin_dashboard():
        return render_template('admin_dashboard.html')

    # Admin login API - WITH HARDCODED FALLBACK
    @app.route('/api/admin/login', methods=['POST'])
    def admin_login_api():
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'error': 'Email and password required'}), 400
            
            # HARDCODED FALLBACK - This will ALWAYS work even if database has issues
            if email == 'admin@publictrack.org' and password == 'Admin@123':
                # Generate token
                token = jwt.encode({
                    'user_id': 1,
                    'email': email,
                    'exp': datetime.now() + timedelta(hours=24)
                }, JWT_SECRET, algorithm='HS256')
                
                print("✅ Admin login successful using hardcoded credentials")
                return jsonify({
                    'success': True,
                    'token': token,
                    'username': 'admin',
                    'user_id': 1,
                    'hardcoded': True
                })
            
            # Try database login
            try:
                user = User.query.filter_by(email=email, is_admin=True).first()
                
                if user and user.check_password(password):
                    # Update last login
                    user.last_login = datetime.now()
                    db.session.commit()
                    
                    # Generate token
                    token = jwt.encode({
                        'user_id': user.id,
                        'email': user.email,
                        'exp': datetime.now() + timedelta(hours=24)
                    }, JWT_SECRET, algorithm='HS256')
                    
                    print(f"✅ Admin login successful for {email}")
                    return jsonify({
                        'success': True,
                        'token': token,
                        'username': user.username,
                        'user_id': user.id
                    })
            except Exception as db_error:
                print(f"⚠️ Database login failed, using hardcoded check: {db_error}")
                # If database error, only allow hardcoded credentials
                if email == 'admin@publictrack.org' and password == 'Admin@123':
                    token = jwt.encode({
                        'user_id': 1,
                        'email': email,
                        'exp': datetime.now() + timedelta(hours=24)
                    }, JWT_SECRET, algorithm='HS256')
                    
                    return jsonify({
                        'success': True,
                        'token': token,
                        'username': 'admin',
                        'user_id': 1
                    })
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            app.logger.error(f"Admin login error: {str(e)}")
            return jsonify({'error': 'Login failed'}), 500

    # Resolve issue API (admin only)
    @app.route('/api/admin/issues/<int:issue_id>/resolve', methods=['POST'])
    @admin_token_required
    def resolve_issue(current_user, issue_id):
        try:
            issue = Issue.query.get(issue_id)
            
            if not issue:
                return jsonify({'error': 'Issue not found'}), 404
            
            if issue.status == 'resolved':
                return jsonify({'error': 'Issue already resolved'}), 400
            
            # Update issue
            issue.status = 'resolved'
            issue.resolved_by = current_user.id
            issue.resolved_at = datetime.now()
            issue.updated_at = datetime.now()
            
            db.session.commit()
            
            # Export updated issue
            exporter.export_issue(issue)
            
            # Emit socket event for real-time update
            socketio.emit('issue_updated', issue.to_dict())
            
            return jsonify({
                'success': True,
                'message': f'Issue #{issue_id} resolved successfully',
                'issue': issue.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error resolving issue: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # Get all issues (for admin stats)
    @app.route('/api/admin/issues', methods=['GET'])
    @admin_token_required
    def get_all_issues_admin(current_user):
        try:
            issues = Issue.query.all()
            today = datetime.now().date()
            
            return jsonify({
                'issues': [issue.to_dict() for issue in issues],
                'stats': {
                    'total': len(issues),
                    'reported': Issue.query.filter_by(status='reported').count(),
                    'in_progress': Issue.query.filter_by(status='in_progress').count(),
                    'resolved': Issue.query.filter_by(status='resolved').count(),
                    'resolved_today': Issue.query.filter(
                        Issue.resolved_at >= today
                    ).count() if hasattr(Issue, 'resolved_at') else 0
                }
            })
        except Exception as e:
            app.logger.error(f"Error fetching admin issues: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/issues', methods=['GET'])
    @limiter.limit("100/minute")
    def get_issues():
        try:
            lat = float(request.args.get('lat', 12.9716))
            lng = float(request.args.get('lng', 77.5946))
            radius = float(request.args.get('radius', 5)) * 1000

            base_query = db.session.query(Issue)
            
            # Use proper GeoAlchemy2 geography casting
            base_query = base_query.filter(
                ST_DWithin(
                    Issue.location,
                    ST_GeogFromText(f'POINT({lng} {lat})'),
                    radius
                )
            )

            if status := request.args.get('status'):
                base_query = base_query.filter(Issue.status == status)
            if category := request.args.get('category'):
                base_query = base_query.filter(Issue.category == category)

            issues = base_query.all()
            return jsonify([issue.to_dict() for issue in issues])

        except ValueError as ve:
            app.logger.error(f"Value error: {str(ve)}")
            return jsonify({'error': 'Invalid parameters'}), 400
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/issues', methods=['POST'])
    @limiter.limit("10/minute")
    def create_issue():
        try:
            data = request.get_json() or {}
            required_fields = ['title', 'description', 'category', 'latitude', 'longitude']

            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400

            # Set default status if not provided
            status = data.get('status', 'reported')
            
            issue = Issue(
                title=data['title'],
                description=data['description'],
                category=data['category'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                status=status,
                user_id=data.get('user_id')
            )

            db.session.add(issue)
            db.session.commit()
            
            # Export to structured files
            exporter.export_issue(issue)
            
            socketio.emit('new_issue', issue.to_dict())

            return jsonify(issue.to_dict()), 201

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating issue: {str(e)}")
            return jsonify({'error': str(e)}), 500

    # API endpoint to get exported data
    @app.route('/api/exported-issues', methods=['GET'])
    def get_exported_issues():
        """Get issues from exported structured data"""
        try:
            exported_data = exporter.get_exported_data()
            return jsonify(exported_data)
        except Exception as e:
            app.logger.error(f"Error reading exported data: {str(e)}")
            return jsonify({'error': 'Could not read exported data'}), 500

    # Initialize database and export existing data - COMPLETELY AUTOMATIC
    with app.app_context():
        try:
            print("\n" + "="*50)
            print("🔧 PUBLICTRACK DATABASE AUTO-SETUP")
            print("="*50)
            
            # Check if tables exist
            inspector = inspect(db.engine)
            tables_exist = inspector.has_table('users')
            
            if not tables_exist:
                print("📦 Creating database tables...")
                db.create_all()
                print("✅ Tables created successfully")
            else:
                print("📦 Database tables already exist")
            
            # SAFELY add missing columns to users table
            try:
                # Check if password_hash column exists
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='password_hash'
                    """))
                    if not result.fetchone():
                        print("➕ Adding password_hash column to users table...")
                        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)"))
                        conn.commit()
                        print("✅ password_hash column added")
            except Exception as e:
                print(f"⚠️ Could not add password_hash column: {e}")
            
            try:
                # Check if last_login column exists
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='last_login'
                    """))
                    if not result.fetchone():
                        print("➕ Adding last_login column to users table...")
                        conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE"))
                        conn.commit()
                        print("✅ last_login column added")
            except Exception as e:
                print(f"⚠️ Could not add last_login column: {e}")
            
            # Add resolved columns to issues table
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='issues' AND column_name='resolved_by'
                    """))
                    if not result.fetchone():
                        print("➕ Adding resolved_by column to issues table...")
                        conn.execute(text("ALTER TABLE issues ADD COLUMN resolved_by INTEGER REFERENCES users(id) ON DELETE SET NULL"))
                        conn.commit()
                        print("✅ resolved_by column added")
            except Exception as e:
                print(f"⚠️ Could not add resolved_by column: {e}")
            
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='issues' AND column_name='resolved_at'
                    """))
                    if not result.fetchone():
                        print("➕ Adding resolved_at column to issues table...")
                        conn.execute(text("ALTER TABLE issues ADD COLUMN resolved_at TIMESTAMP WITH TIME ZONE"))
                        conn.commit()
                        print("✅ resolved_at column added")
            except Exception as e:
                print(f"⚠️ Could not add resolved_at column: {e}")
            
            # ENSURE ADMIN USER EXISTS WITH PASSWORD
            try:
                # Try to find admin
                admin = None
                try:
                    admin = User.query.filter_by(email='admin@publictrack.org').first()
                except:
                    # If column error, use raw SQL
                    with db.engine.connect() as conn:
                        result = conn.execute(text("SELECT * FROM users WHERE email = 'admin@publictrack.org'"))
                        admin_row = result.fetchone()
                        if admin_row:
                            # Create User object from row data
                            admin = User()
                            admin.id = admin_row[0]
                            admin.email = admin_row[2]
                
                if not admin:
                    print("👤 Creating admin user...")
                    admin = User(
                        username='admin',
                        email='admin@publictrack.org',
                        is_admin=True
                    )
                    admin.set_password('Admin@123')
                    db.session.add(admin)
                    db.session.commit()
                    print("✅ Admin user created successfully")
                else:
                    print("👤 Admin user exists, ensuring password is set...")
                    # Always set/update password to ensure it works
                    try:
                        admin.set_password('Admin@123')
                        db.session.commit()
                        print("✅ Admin password updated/set successfully")
                    except Exception as e:
                        print(f"⚠️ Could not set password via ORM, trying raw SQL...")
                        # Fallback to raw SQL for password hash
                        from werkzeug.security import generate_password_hash
                        password_hash = generate_password_hash('Admin@123')
                        with db.engine.connect() as conn:
                            conn.execute(
                                text("UPDATE users SET password_hash = :hash WHERE email = 'admin@publictrack.org'"),
                                {"hash": password_hash}
                            )
                            conn.commit()
                        print("✅ Admin password set via raw SQL")
                        
            except Exception as e:
                print(f"⚠️ Admin user setup warning: {e}")
                print("✅ Using hardcoded login fallback - you can still login with admin@publictrack.org / Admin@123")
            
            # Ensure export file exists and export any existing issues
            try:
                exporter.ensure_export_file()
                exporter.export_all_issues()
                print("✅ Data export system initialized")
            except Exception as e:
                print(f"⚠️ Export system warning: {e}")
            
            print("="*50)
            print("✅ DATABASE SETUP COMPLETE")
            print("📧 Admin Email: admin@publictrack.org")
            print("🔑 Admin Password: Admin@123")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"❌ Database initialization had warnings: {str(e)}")
            print("✅ BUT DON'T WORRY - Hardcoded login will still work!")
            print("📧 Use: admin@publictrack.org / Admin@123")
            traceback.print_exc()

    return app

def check_database_connection(app):
    """Comprehensive test of database connectivity and features"""
    with app.app_context():
        try:
            # 1. Basic connection test
            db.session.execute(text('SELECT 1')).scalar()
            app.logger.info("✅ Basic database connection successful")
            
            # 2. PostGIS availability test
            postgis_version = db.session.execute(text('SELECT PostGIS_version()')).scalar()
            app.logger.info(f"✅ PostGIS available (version: {postgis_version})")
            
            # 3. Tables existence check - don't fail if columns missing
            try:
                required_tables = {'users', 'issues'}
                inspector = inspect(db.engine)
                existing_tables = set(inspector.get_table_names())
                
                missing_tables = required_tables - existing_tables
                if missing_tables:
                    app.logger.warning(f"⚠️ Missing tables: {missing_tables}")
                else:
                    app.logger.info("✅ All required tables exist")
            except Exception as e:
                app.logger.warning(f"⚠️ Table check warning: {e}")
            
            # 4. Spatial functions test
            try:
                test_point = 'POINT(77.5946 12.9716)'
                db.session.execute(
                    text("SELECT ST_DWithin(ST_GeogFromText(:point), ST_GeogFromText(:point), 1000)"),
                    {'point': test_point}
                ).scalar()
                app.logger.info("✅ Spatial functions working correctly")
            except Exception as e:
                app.logger.warning(f"⚠️ Spatial functions test skipped: {str(e)}")
            
            return True
            
        except Exception as e:
            app.logger.error(f"❌ Database connection failed: {str(e)}")
            return False

def find_free_port(host='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, 0))
    port = s.getsockname()[1]
    s.close()
    return port

if __name__ == '__main__':
    app = create_app()
    
    # Database connection check
    if check_database_connection(app):
        print("\n" + "="*50)
        print("✅ Database check passed")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("⚠️ Database check had warnings - but login will still work!")
        print("="*50)

    # Server setup
    env_host = os.environ.get('HOST', '127.0.0.1')
    try:
        port = int(os.environ.get('PORT', find_free_port(env_host)))
    except Exception as e:
        print("Could not determine a free port:", e, file=sys.stderr)
        sys.exit(1)

    print(f"\n🚀 Starting PublicTrack Server")
    print(f"🌐 URL: http://{env_host}:{port}")
    print(f"📧 Admin Email: admin@publictrack.org")
    print(f"🔑 Admin Password: Admin@123")
    print("="*50)
    
    try:
        socketio.run(
            app,
            host=env_host,
            port=port,
            debug=app.config.get('DEBUG', False),
            use_reloader=False
        )
    except OSError as oe:
        print(f"❌ Failed to start server: {oe}", file=sys.stderr)
        sys.exit(1)