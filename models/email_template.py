from extensions import db
from datetime import datetime

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    template_type = db.Column(db.String(50), unique=True, nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_default_templates():
        return {
            'visitor_confirmation': {
                'subject': 'Welcome to Refresh Church!',
                'html_content': '''
                    <h2>Welcome to Refresh Church!</h2>
                    <p>Dear {{ visitor.first_name }},</p>
                    <p>Thank you for registering to visit us! We're looking forward to meeting you on {{ visitor.visit_date.strftime('%A, %B %d, %Y') }}.</p>
                    <p>Service Time: {{ config.SERVICE_TIME }}</p>
                    <p>Address: {{ config.CHURCH_ADDRESS }}</p>
                    <p>If you have any questions, please don't hesitate to contact us:</p>
                    <ul>
                        <li>Phone: {{ config.CHURCH_PHONE }}</li>
                        <li>Website: {{ config.CHURCH_WEBSITE }}</li>
                    </ul>
                '''
            },
            'staff_notification': {
                'subject': 'New Visit Registration',
                'html_content': '''
                    <h2>New Visitor Registration</h2>
                    <p><strong>Name:</strong> {{ visitor.first_name }} {{ visitor.last_name }}</p>
                    <p><strong>Email:</strong> {{ visitor.email }}</p>
                    <p><strong>Phone:</strong> {{ visitor.phone }}</p>
                    <p><strong>Visit Date:</strong> {{ visitor.visit_date.strftime('%A, %B %d, %Y') }}</p>
                    {% if visitor.children %}
                    <h3>Registered Children:</h3>
                    <ul>
                    {% for child in visitor.children %}
                        <li>{{ child.first_name }} {{ child.last_name }} (DOB: {{ child.date_of_birth.strftime('%Y-%m-%d') }})
                        {% if child.special_instructions %}
                        <br>Special Instructions: {{ child.special_instructions }}
                        {% endif %}
                        </li>
                    {% endfor %}
                    </ul>
                    {% endif %}
                '''
            }
        }
