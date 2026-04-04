# init_database.py
import psycopg2
import sys

def init_database():
    print("🚀 Initializing PublicTrack Database...")
    
    try:
        # Connect to PostgreSQL with password
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="123",  # Your password
            database="publictrack",
            port=5432
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL")
        
        # SQL commands to set up the database
        sql_commands = [
            # 1. Install PostGIS extension
            "CREATE EXTENSION IF NOT EXISTS postgis;",
            
            # 2. Create users table
            """CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                is_admin BOOLEAN DEFAULT false NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );""",
            
            # 3. Create issues table
            """CREATE TABLE IF NOT EXISTS issues (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(50) NOT NULL CHECK (category IN ('roads', 'water', 'garbage', 'lighting', 'safety', 'obstructions')),
                latitude FLOAT NOT NULL CHECK (latitude BETWEEN -90 AND 90),
                longitude FLOAT NOT NULL CHECK (longitude BETWEEN -180 AND 180),
                location GEOMETRY(POINT, 4326) NOT NULL,
                status VARCHAR(20) DEFAULT 'reported' NOT NULL CHECK (status IN ('reported', 'in_progress', 'resolved')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
            );""",
            
            # 4. Create indexes
            "CREATE INDEX IF NOT EXISTS idx_issues_location ON issues USING GIST(location);",
            "CREATE INDEX IF NOT EXISTS idx_issues_category ON issues(category);",
            "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);",
            
            # 5. Create location update function
            """CREATE OR REPLACE FUNCTION update_issue_location()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
                NEW.updated_at := CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;""",
            
            # 6. Create trigger
            "DROP TRIGGER IF EXISTS trg_issue_location ON issues;",
            """CREATE TRIGGER trg_issue_location
            BEFORE INSERT OR UPDATE ON issues
            FOR EACH ROW EXECUTE FUNCTION update_issue_location();""",
            
            # 7. Insert admin user
            """INSERT INTO users (username, email, is_admin)
            VALUES ('admin', 'admin@publictrack.org', true)
            ON CONFLICT (username) DO NOTHING;"""
        ]
        
        print("📋 Setting up database schema...")
        
        # Execute each SQL command
        for i, command in enumerate(sql_commands, 1):
            try:
                cursor.execute(command)
                print(f"  ✅ Step {i}: Executed")
            except Exception as e:
                # If it's a "already exists" error, that's fine
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print(f"  ✓ Step {i}: Already exists")
                else:
                    print(f"  ⚠ Step {i}: Note - {str(e)[:80]}")
        
        print("✅ Database schema created successfully!")
        
        # Verify setup
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = cursor.fetchall()
        print(f"📊 Tables created: {[t[0] for t in tables if t[0] not in ['geography_columns', 'geometry_columns', 'spatial_ref_sys']]}")
        
        # Check PostGIS version
        cursor.execute("SELECT PostGIS_version();")
        postgis_version = cursor.fetchone()[0]
        print(f"🗺 PostGIS version: {postgis_version}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PublicTrack Database Initialization")
    print("=" * 50)
    
    if init_database():
        print("\n" + "=" * 50)
        print("🎉 SUCCESS: PublicTrack database initialized!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open http://localhost:5000 in your browser")
        print("3. Or use the port shown when app starts")
    else:
        print("\n" + "=" * 50)
        print("💥 FAILED: Database initialization failed!")
        print("=" * 50)
        print("\nTroubleshooting:")
        print("1. Check PostgreSQL is running: net start | findstr postgres")
        print("2. Verify password in this script matches your PostgreSQL password")
        print("3. Check database 'publictrack' exists in pgAdmin")
        sys.exit(1)