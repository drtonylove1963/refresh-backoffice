from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from src.core.extensions import db
from src.utils.helpers.timezone_utils import format_datetime, format_date

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': format_datetime(self.created_at)
        }

class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    breeze_id = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    profile_image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    church_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    gender = db.Column(db.String(20))
    marital_status = db.Column(db.String(50))
    address = db.Column(db.String(200))
    grade = db.Column(db.String(50))
    employer = db.Column(db.String(100))
    baptism_date = db.Column(db.DateTime)
    membership_date = db.Column(db.DateTime)
    vb_viewed_intro_date = db.Column(db.DateTime)
    vb_session1_date = db.Column(db.DateTime)
    vb_session2_date = db.Column(db.DateTime)
    vb_session3_date = db.Column(db.DateTime)
    family_members = db.Column(db.JSON)

    def __repr__(self):
        return f'<Member {self.first_name} {self.last_name}>'

    @staticmethod
    def from_breeze_data(data):
        """Create or update a Member from Breeze API data"""
        return {
            'breeze_id': str(data.get('id')),
            'first_name': data.get('force_first'),
            'last_name': data.get('force_last'),
            'email': data.get('details', {}).get('email'),
            'phone': data.get('details', {}).get('mobile_phone') or data.get('details', {}).get('home_phone'),
            'profile_image': data.get('details', {}).get('path'),
            'is_active': data.get('status') == 'active',
            'church_status': data.get('details', {}).get('membership_status'),
            'updated_at': datetime.utcnow()
        }

    def to_dict(self):
        return {
            'id': self.id,
            'breeze_id': self.breeze_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'profile_image': self.profile_image,
            'gender': self.gender,
            'marital_status': self.marital_status,
            'address': self.address,
            'grade': self.grade,
            'employer': self.employer,
            'church_status': self.church_status,
            'baptism_date': format_date(self.baptism_date) if self.baptism_date else None,
            'membership_date': format_date(self.membership_date) if self.membership_date else None,
            'vb_viewed_intro_date': format_datetime(self.vb_viewed_intro_date) if self.vb_viewed_intro_date else None,
            'vb_session1_date': format_datetime(self.vb_session1_date) if self.vb_session1_date else None,
            'vb_session2_date': format_datetime(self.vb_session2_date) if self.vb_session2_date else None,
            'vb_session3_date': format_datetime(self.vb_session3_date) if self.vb_session3_date else None,
            'family_members': self.family_members,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at)
        }

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50))
    subject = db.Column(db.String(200))
    html_content = db.Column(db.Text)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'template_type': self.template_type,
            'subject': self.subject,
            'html_content': self.html_content,
            'modified_at': format_datetime(self.modified_at),
            'created_at': format_datetime(self.created_at)
        }

    @staticmethod
    def get_default_templates():
        return [
            {
                'template_type': 'visitor_welcome',
                'subject': 'Welcome to Refresh Church!',
                'html_content': '''
                    <p>Dear {first_name},</p>
                    <p>Welcome to Refresh Church! We're so glad you visited us.</p>
                    <p>Best regards,<br>Refresh Church Team</p>
                '''
            },
            {
                'template_type': 'visitor_followup',
                'subject': 'Following up from your visit to Refresh Church',
                'html_content': '''
                    <p>Dear {first_name},</p>
                    <p>We hope you enjoyed your visit to Refresh Church!</p>
                    <p>Best regards,<br>Refresh Church Team</p>
                '''
            }
        ]
