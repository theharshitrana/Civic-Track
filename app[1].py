from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_MakePoint
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://civictrack_user:securepassword@localhost:5432/civictrack')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

db = SQLAlchemy(app)

class Issue(db.Model):
    __tablename__ = 'issues'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    location = db.Column(Geography('POINT', srid=4326))
    status = db.Column(db.String(20), default='reported')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<Issue {self.id}: {self.title}>'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/issues', methods=['GET'])
def get_issues():
    try:
        # Get parameters with defaults
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', default=5, type=float)  # in km
        status = request.args.get('status')
        category = request.args.get('category')

        # Validate required parameters
        if lat is None or lng is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400

        # Create point and base query
        point = ST_MakePoint(lng, lat)
        query = Issue.query.filter(ST_DWithin(Issue.location, point, radius * 1000))

        # Apply filters if provided
        if status:
            query = query.filter(Issue.status == status)
        if category:
            query = query.filter(Issue.category == category)

        # Execute query
        issues = query.all()

        # Format response
        issues_data = [{
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'category': issue.category,
            'latitude': db.session.scalar(issue.location.ST_Y()),
            'longitude': db.session.scalar(issue.location.ST_X()),
            'status': issue.status,
            'created_at': issue.created_at.isoformat() if issue.created_at else None,
            'updated_at': issue.updated_at.isoformat() if issue.updated_at else None
        } for issue in issues]

        return jsonify(issues_data)

    except Exception as e:
        app.logger.error(f"Error fetching issues: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/issues', methods=['POST'])
def create_issue():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['title', 'description', 'category']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate field content
        if not data['title'].strip() or not data['description'].strip():
            return jsonify({'error': 'Title and description cannot be empty'}), 400

        # Create new issue
        new_issue = Issue(
            title=data['title'].strip(),
            description=data['description'].strip(),
            category=data['category'],
            location=ST_MakePoint(
                float(data.get('longitude', 0)),
                float(data.get('latitude', 0))
            ),
            status='reported'
        )

        db.session.add(new_issue)
        db.session.commit()

        return jsonify({
            'id': new_issue.id,
            'message': 'Issue created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating issue: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Add some initial categories if needed
        if not Issue.query.first():
            sample_issue = Issue(
                title='Sample Issue',
                description='This is a sample issue',
                category='roads',
                location=ST_MakePoint(77.5946, 12.9716),
                status='reported'
            )
            db.session.add(sample_issue)
            db.session.commit()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)