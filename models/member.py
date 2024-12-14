from extensions import db
from datetime import datetime
from enum import Enum

class Role(Enum):
    ADMIN = 'admin'
    STAFF = 'staff'
    MEMBER = 'member'

class Member(db.Model):
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    breeze_id = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(50))
    role = db.Column(db.Enum(Role), default=Role.MEMBER)
    is_active = db.Column(db.Boolean, default=True)
    photo_url = db.Column(db.String(500))
    
    # Address information
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip = db.Column(db.String(20))
    
    # Important dates
    membership_date = db.Column(db.Date)
    baptism_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_edit(self, current_user):
        """Check if the current user can edit this member"""
        return current_user.role == Role.ADMIN
    
    def to_dict(self):
        """Convert member to dictionary for API responses"""
        return {
            'id': self.id,
            'breeze_id': self.breeze_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
