PublicTrack - Community Issue Reporting System

A full-stack web application for citizens to report local issues and municipal authorities to manage them in real-time. This platform bridges the gap between community needs and administrative action through interactive mapping and live data synchronization.

🚀 Features

For Citizens
    • Interactive Map: Visualize reported issues on an interactive Leaflet.js map.

    • Real-time Updates: Live updates using Socket.IO when new issues are reported.

    • Advanced Search: Search addresses using OpenStreetMap Nominatim with smart suggestions.

    • Issue Filtering: Filter by category, status, and radius (1-50km).

    • One-click Reporting: Click on map, fill form, submit issue.

    • Address Autocomplete: Smart address suggestions with icons and categories.

    • Theme Support: Light and dark themes with persistent storage.

    • Responsive Design: Works seamlessly on desktop, tablet, and mobile.

For Administrators

    • Secure Admin Login: JWT-based authentication with password hashing.

    • Admin Dashboard: Dedicated interface for municipal authorities.

    • Resolution Mode: Toggle to select and resolve issues.

    • Real-time Resolution: Mark issues as resolved with one click.

    • Live Updates: Resolved issues instantly update on the public map.

    • Statistics Dashboard: View total, pending, and resolved issues.

    • Data Export: Export issues to JSON format.

    • Print Reports: Generate printable issue reports.

    • Quick Filters: Click on stats to filter by status.

    • Tour Guide: Interactive tutorial for new admin users.

🛠️ Tech Stack

Backend

    • Python 3.10+ with Flask framework

    • PostgreSQL 14+ with PostGIS extension

    • SQLAlchemy ORM with GeoAlchemy2

    • Flask-SocketIO for real-time communication

    • JWT for secure admin authentication

    • Flask-Limiter for API rate limiting

    • Werkzeug for password hashing

Frontend

    • Leaflet.js for interactive maps

    • Vanilla JavaScript (ES6+)

    • CSS3 with custom properties, grid, and flexbox

    • Font Awesome 6 for icons

    • Socket.IO client for real-time updates

Database

    • PostGIS for spatial queries and geography types.

    • Database Triggers for automatic location updates.

    • Foreign Key Constraints with ON DELETE SET NULL.

    • Composite Indexes for optimized spatial queries.

📁 Project Structure

PublicTrack/

├── app.py                     # Main Flask application (auto-setup)

├── config.py                  # Configuration settings

├── models.py                  # Database models with spatial support

├── extensions.py              # Flask extensions initialization

├── data_exporter.py           # JSON/CSV export functionality

├── init_database.py           # Database initialization script

├── requirements.txt           # Python dependencies

├── .env                       # Environment variables

├── .flaskenv                  # Flask environment

├── publictrack_issues_export.json

├── publictrack_issues_export.csv

├── static/

│   ├── css/

│   │   └── styles.css         # Main stylesheet with theme support

│   ├── js/

│   │   └── main.js           # Frontend JavaScript

│   └── images/

│       ├── logo.png           # Application logo

│       └── favicon.png        # Browser favicon

└── templates/

    ├── index.html             # Main public interface

    ├── admin_login.html       # Admin login page

    └── admin_dashboard.html   # Admin management interface

🚀 Quick Start

Prerequisites

    • Python 3.10 or higher

    • PostgreSQL 14+ with PostGIS extension

Installation

    • Clone the project

        • git clone https://github.com/Abhinav15092005/publictrack.git
        
        • cd publictrack
        
        • Install dependencies

    • Install dependencies

        • pip install -r requirements.txt
    
    • Set up PostgreSQL

        Create a database named publictrack.

        Update .env file with your credentials:

            • FLASK_ENV=development
    
            • DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/publictrack
            
            • SECRET_KEY=your-secret-key-here
    
    • Initialize & Run

        python init_database.py

        python app.py
        
        🔑 Default Admin Credentials

        Email: admin@publictrack.org

        Password: Admin@123

📊 API Endpoints

    Public Endpoints
    
        Method	   | Endpoint	                    | Description
    
        GET	       | /	                            | Public map interface
    
        GET	       | /api/issues	                | Get issues within radius
    
        POST	   | /api/issues	                | Create new issue
    
        GET	       | /api/exported-issues	        | Get exported data
    
    Admin Endpoints

        Method	| Endpoint	                           | Description

        GET	    | /admin/login	                       | Admin login page

        POST	| /api/admin/login	                   | Admin authentication

        GET	    | /admin/dashboard	                   | Admin management interface

        POST	| /api/admin/issues/[id]/resolve	   | Resolve an issue

        GET	    | /api/admin/issues	                   | Get all issues with stats

🎯 Usage Guide

Public User

    • Open the main page.

    • Search for an address or click directly on the map.

    • Fill in issue details (title, description, category).

    • Click "Submit Report".

    • Watch your issue appear on the map in real-time.

Admin User

    • Click the admin slider button in the header.

    • Login with admin credentials.

    • Toggle "Resolution Mode" using the slider.

    • Click any issue marker to select it.

    • Click "Mark as Resolved" to update.

🔒 Security & Data

    • Data Export: Automatic JSON/CSV export on every issue creation for BI tools and analytics.

    • Security: Uses password hashing (Werkzeug), JWT tokens, and API rate limiting (Flask-Limiter).

    • Automatic Setup: app.py handles table creation and missing column migrations automatically.

🐛 Troubleshooting

    • Database connection errors: Verify PostgreSQL is running and the PostGIS extension is enabled via psql -d publictrack -c "SELECT PostGIS_version();".

    • Login Issues: Ensure the .env SECRET_KEY is set. If locked out, use the default fallback credentials.

    • Port in use: The app will automatically attempt to find the next available port if 5000 is occupied.