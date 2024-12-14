from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()
