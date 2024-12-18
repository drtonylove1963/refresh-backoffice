"""
Flask extensions initialization.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from src.models import Admin  # Import here to avoid circular imports
    return Admin.query.get(int(user_id))
