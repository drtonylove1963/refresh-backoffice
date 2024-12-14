from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    children = db.relationship('Child', backref='visitor', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    special_instructions = db.Column(db.Text)
    visitor_id = db.Column(db.Integer, db.ForeignKey('visitor.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), nullable=False, unique=True)  # 'staff_notification' or 'visitor_confirmation'
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    modified_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_default_templates():
        return {
            'staff_notification': {
                'subject': 'New Visit Registration',
                'html_content': '''
                    <h2>New Visit Registration</h2>
                    <p>A new visitor has registered for an upcoming visit:</p>
                    <p><strong>Name:</strong> {{ visitor.first_name }} {{ visitor.last_name }}</p>
                    <p><strong>Email:</strong> {{ visitor.email }}</p>
                    <p><strong>Phone:</strong> {{ visitor.phone }}</p>
                    <p><strong>Visit Date:</strong> {{ visitor.visit_date.strftime('%Y-%m-%d') }}</p>
                    {% if visitor.children %}
                    <h3>Registered Children:</h3>
                    {% for child in visitor.children %}
                    <p>• {{ child.first_name }} {{ child.last_name }} (DOB: {{ child.date_of_birth.strftime('%Y-%m-%d') }})<br>
                    Notes: {{ child.special_instructions or 'None' }}</p>
                    {% endfor %}
                    {% endif %}
                    <p>Please ensure the welcome team is notified and prepared for this visit.</p>
                '''
            },
            'visitor_confirmation': {
                'subject': 'Welcome to Refresh Church!',
                'html_content': '''
                    <h2>Thank you for planning your visit to Refresh Church!</h2>
                    <p>We're excited to welcome you on {{ visitor.visit_date.strftime('%Y-%m-%d') }}.</p>
                    <p><strong>Service Time:</strong> {{ config.SERVICE_TIME }}</p>
                    <p><strong>Location:</strong> {{ config.CHURCH_ADDRESS }}</p>
                    <p>If you have any questions before your visit, please contact us at {{ config.CHURCH_PHONE }}.</p>
                '''
            }
        }
