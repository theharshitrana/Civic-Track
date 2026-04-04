import os
import json
import csv
from datetime import datetime
from extensions import db
from models import Issue
from sqlalchemy import inspect

class DataExporter:
    def __init__(self, app=None):
        self.app = app
        self.export_file = 'publictrack_issues_export.json'
        self.csv_file = 'publictrack_issues_export.csv'
        
    def init_app(self, app):
        self.app = app
        
    def ensure_export_file(self):
        """Create export file if it doesn't exist"""
        if not os.path.exists(self.export_file):
            base_structure = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "PublicTrack Issues Export - Structured data for analytics",
                    "project": "PublicTrack",
                    "export_format": "JSON/CSV for database import and analytics"
                },
                "schema": {
                    "Year": "int",
                    "Month": "str", 
                    "Day": "str",
                    "Date": "str",
                    "Time": "str",
                    "id": "int",
                    "title": "str",
                    "description": "str", 
                    "category": "str",
                    "latitude": "float",
                    "longitude": "float",
                    "status": "str",
                    "created_at": "str",
                    "updated_at": "str",
                    "user_id": "int"
                },
                "issues": []
            }
            with open(self.export_file, 'w', encoding='utf-8') as f:
                json.dump(base_structure, f, indent=2)
            
            # Also create CSV with headers
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Year', 'Month', 'Day', 'Date', 'Time', 'id', 'title', 
                    'description', 'category', 'latitude', 'longitude', 
                    'status', 'created_at', 'updated_at', 'user_id'
                ])
            print(f"✅ Created new export files: {self.export_file}, {self.csv_file}")
        else:
            print(f"✅ Export files already exist: {self.export_file}, {self.csv_file}")
                
        return True
    
    def parse_datetime(self, dt_string):
        """Parse datetime string into structured components"""
        if isinstance(dt_string, str):
            try:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            except:
                dt = datetime.now()
        else:
            dt = dt_string
            
        return {
            'year': dt.year,
            'month': dt.strftime('%B'),
            'day': dt.strftime('%A'),
            'date': dt.strftime('%Y-%m-%d'),
            'time': dt.strftime('%H:%M:%S.%f')[:-3]  # Hour:Minute:Second.Millisecond
        }
    
    def export_issue(self, issue):
        """Export a single issue to structured files"""
        self.ensure_export_file()
        
        # Parse datetime components
        dt_components = self.parse_datetime(issue.created_at.isoformat() if issue.created_at else datetime.now().isoformat())
        
        # Prepare structured data
        structured_issue = {
            'Year': dt_components['year'],
            'Month': dt_components['month'],
            'Day': dt_components['day'],
            'Date': dt_components['date'],
            'Time': dt_components['time'],
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'category': issue.category,
            'latitude': float(issue.latitude),
            'longitude': float(issue.longitude),
            'status': issue.status,
            'created_at': issue.created_at.isoformat() if issue.created_at else '',
            'updated_at': issue.updated_at.isoformat() if issue.updated_at else '',
            'user_id': issue.user_id
        }
        
        # Update JSON file
        try:
            with open(self.export_file, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                # Check if issue already exists
                existing_ids = [iss.get('id') for iss in data['issues']]
                if issue.id not in existing_ids:
                    data['issues'].append(structured_issue)
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                    print(f"✅ Exported issue #{issue.id} to JSON")
        except Exception as e:
            print(f"❌ Error updating JSON file: {e}")
        
        # Update CSV file
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    structured_issue['Year'],
                    structured_issue['Month'],
                    structured_issue['Day'],
                    structured_issue['Date'],
                    structured_issue['Time'],
                    structured_issue['id'],
                    structured_issue['title'],
                    structured_issue['description'],
                    structured_issue['category'],
                    structured_issue['latitude'],
                    structured_issue['longitude'],
                    structured_issue['status'],
                    structured_issue['created_at'],
                    structured_issue['updated_at'],
                    structured_issue['user_id']
                ])
            print(f"✅ Exported issue #{issue.id} to CSV")
        except Exception as e:
            print(f"❌ Error updating CSV file: {e}")
        
        return structured_issue
    
    def export_all_issues(self):
        """Export all existing issues to structured files"""
        with self.app.app_context():
            try:
                issues = Issue.query.all()
                print(f"📊 Exporting {len(issues)} existing issues to structured files...")
                for issue in issues:
                    self.export_issue(issue)
                print("✅ All existing issues exported successfully")
            except Exception as e:
                print(f"❌ Error exporting existing issues: {e}")
    
    def get_exported_data(self):
        """Get all exported data for map display"""
        if not os.path.exists(self.export_file):
            return []
        
        try:
            with open(self.export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('issues', [])
        except Exception as e:
            print(f"❌ Error reading exported data: {e}")
            return []

# Global exporter instance
exporter = DataExporter()