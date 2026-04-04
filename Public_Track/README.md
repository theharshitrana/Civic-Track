PublicTrack - Community Issue Reporting System



🚀 Features:

1\. Interactive Map: Visualize reported issues on an interactive Leaflet.js map

2\. Real-time Updates: Live updates using Socket.IO when new issues are reported

3\. Advanced Search: Search addresses using OpenStreetMap Nominatim

4\. Issue Filtering: Filter by category, status, and radius

5\. Data Export: Automatic export to JSON and CSV formats

6\. Responsive Design: Works on desktop and mobile devices

7\. Theme Support: Light and dark themes

8\. Passwordless Authentication: Simple user management



🛠️ Tech Stack:

Backend:

1\. Python 3.10+ with Flask web framework

2\. PostgreSQL with PostGIS for spatial data

3\. SQLAlchemy ORM for database operations

4\. Flask-SocketIO for real-time communication

5\. Flask-Limiter for API rate limiting



Frontend:

1\. Leaflet.js for interactive maps

2\. Vanilla JavaScript with modern ES6+ features

3\. CSS3 with custom properties and grid/flexbox

4\. Font Awesome icons



Database:

1\. PostgreSQL 14+ with PostGIS extension

2\. GeoAlchemy2 for spatial queries

3\. Automatic triggers for location updates



📁 Project Structure:

&nbsp;   PublicTrack/

&nbsp;   ├── app.py                    # Main Flask application

&nbsp;   ├── config.py                 # Configuration settings

&nbsp;   ├── models.py                 # Database models

&nbsp;   ├── extensions.py             # Flask extensions

&nbsp;   ├── data\_exporter.py          # Data export functionality

&nbsp;   ├── init\_database.py          # Database initialization

&nbsp;   ├── requirements.txt          # Python dependencies

&nbsp;   ├── .env                      # Environment variables

&nbsp;   ├── .flaskenv                 # Flask environment

&nbsp;   ├── static/

&nbsp;   │   ├── css/

&nbsp;   │   │   └── styles.css        # Main stylesheet

&nbsp;   │   ├── js/

&nbsp;   │   │   └── main.js           # Frontend JavaScript

&nbsp;   │   └── images/               # Logo and icons

&nbsp;   └── templates/

&nbsp;       └── index.html            # Main HTML template



🚀 Quick Start:

Prerequisites:

1\. Python 3.10+

2\. PostgreSQL 14+ with PostGIS

3\. Git



Installation:

1\. Clone the repository:

&nbsp;   git clone https://github.com/Abhinav15092005/publictrack.git

&nbsp;   cd publictrack

2\. Install Python dependencies:

&nbsp;   pip install -r requirements.txt

3\. Set up PostgreSQL:

&nbsp;   - Install PostgreSQL with PostGIS extension

&nbsp;   - Create a database named `publictrack`

&nbsp;   - Update the `.env` file with your database credentials

&nbsp;   - Initialize the database:

&nbsp;       python init\_database.py

4\. Run the application:

&nbsp;   python app.py

5\. Open in browser:

&nbsp;   Navigate to http://localhost:5000 (or the port shown in terminal)



⚙️ Configuration:

Environment Variables:

&nbsp;   FLASK\_ENV=development

&nbsp;   DATABASE\_URL=postgresql://postgres:password@localhost:5432/publictrack

&nbsp;   SECRET\_KEY=your-secret-key-here



Database Setup:

&nbsp;   CREATE EXTENSION postgis;



📊 Features in Detail:

1\. Issue Reporting:

&nbsp;   - Click on map to select location

&nbsp;   - Fill in issue details (title, description, category)

&nbsp;   - Automatic address lookup

&nbsp;   - Real-time notification to other users

2\. Issue Categories:

&nbsp;   - 🚧 Roads: Potholes, traffic issues

&nbsp;   - 💧 Water: Supply problems, flooding

&nbsp;   - 🗑️ Garbage: Waste management, littering

&nbsp;   - 💡 Lighting: Streetlight outages

&nbsp;   - 🛡️ Safety: Hazards, security concerns

&nbsp;   - 🚧 Obstructions: Blocked paths, sidewalks

3\. Filtering System:

&nbsp;   - Radius filter (1-50km from center)

&nbsp;   - Status filter (reported/in progress/resolved)

&nbsp;   - Category filter

&nbsp;   - Real-time map updates

4\. Data Export:

&nbsp;   - Automatic export to JSON and CSV

&nbsp;   - Structured data for analytics

&nbsp;   - Monthly and yearly breakdowns

&nbsp;   - Easy import to other systems



🔧 API Endpoints:

\- GET /api/issues            Get issues within radius

\- POST /api/issues           Create new issue

\- GET /api/exported-issues   Get exported data



Example API Request:

&nbsp;   # Get issues within 5km of coordinates

&nbsp;   GET /api/issues?lat=12.9716\&lng=77.5946\&radius=5



🤝 Contributing:

1\. Fork the repository

2\. Create a feature branch: git checkout -b feature/AmazingFeature

3\. Commit changes: git commit -m 'Add AmazingFeature'

4\. Push to branch: git push origin feature/AmazingFeature

5\. Open a Pull Request



