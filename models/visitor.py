from extensions import db
from datetime import datetime

class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with Child model
    children = db.relationship('Child', backref='visitor', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitors.id'), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    special_instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
