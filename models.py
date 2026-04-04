from datetime import datetime
from extensions import db
from geoalchemy2 import Geometry
from flask_login import UserMixin
from sqlalchemy import func, event
from werkzeug.security import generate_password_hash, check_password_hash

class Issue(db.Model):
    __tablename__ = 'issues'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location = db.Column(Geometry('POINT', srid=4326), nullable=False)
    status = db.Column(db.String(20), default='reported', nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id,
            'resolved_by': self.resolved_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

@event.listens_for(Issue, 'before_insert')
@event.listens_for(Issue, 'before_update')
def validate_issue(mapper, connection, target):
    # Validate coordinates
    if not (-90 <= target.latitude <= 90 and -180 <= target.longitude <= 180):
        raise ValueError("Coordinates out of valid range (-90 to 90 lat, -180 to 180 lng)")
    
    # Validate category
    valid_categories = ['roads', 'water', 'garbage', 'lighting', 'safety', 'obstructions']
    if target.category not in valid_categories:
        raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
    
    # FIX: Better status handling - default to 'reported' if not set
    valid_statuses = ['reported', 'in_progress', 'resolved']
    if not target.status:
        target.status = 'reported'
    
    if target.status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")