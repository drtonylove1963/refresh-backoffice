from flask import Blueprint

# Create blueprint objects
main_bp = Blueprint('main', __name__, template_folder='templates')
admin_bp = Blueprint('admin', __name__, template_folder='templates')
member_bp = Blueprint('member', __name__, template_folder='templates')

# Import routes after blueprint creation to avoid circular imports
from . import main_routes
from . import admin_routes
from . import member_routes

# List all blueprints that need to be registered
blueprints = [main_bp, admin_bp, member_bp]
