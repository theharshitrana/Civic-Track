# 🌐 CivicTrack - Community Issue Reporting System

CivicTrack is a web-based platform that allows citizens to report and track civic issues in their locality—such as potholes, garbage accumulation, water leaks, and broken streetlights. It promotes transparency, accountability, and quick response by enabling real-time issue tracking and progress monitoring.

a
---

## ✅ Features

- 📍 Interactive map showing reported issues (via Leaflet.js)
- 📝 Easy issue reporting with description, category & location
- 🔎 Filter issues by status, category, and proximity
- 🔄 Status tracking: Reported → In Progress → Resolved
- 👤 Role-based access: Citizens, Municipal Workers, Admins
- 📱 Fully responsive design for mobile, tablet, and desktop

---

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Leaflet.js)
- **Backend**: Python (Flask), SQLAlchemy
- **Database**: PostgreSQL with PostGIS (for geolocation support)
- **Deployment**: Compatible with Render, Heroku, or AWS

---

## ⚙️ Setup

1. **Install dependencies**
   ```bash
   pip install flask flask-sqlalchemy psycopg2-binary geoalchemy2 python-dotenv
2. **Set up PostgreSQL and PostGIS**
   ```sql
   CREATE EXTENSION postgis;
3. **Run the app**
   ```bash
   python app.py
5. **Open in browser**: http://localhost:5000

---

## 👥 Usage
- **Citizens**: Submit local issues through a simple form
- **Municipal Staff**: Update progress and resolve issues
- **Admins**: Manage issue categories and user roles
