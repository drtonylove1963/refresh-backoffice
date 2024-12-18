# Package initialization
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from src.core.extensions import db, mail, csrf, login_manager, migrate
from src.config import Config
from src.services.breeze_service import BreezeAPI
from src.routes import blueprints, register_template_filters
from flask_wtf.csrf import generate_csrf, CSRFError
from src.models import Admin

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register template filters
    register_template_filters(app)

    # Register blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Set up login manager
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    # Handle CSRF errors
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/csrf_error.html', reason=e.description), 400

    return app
