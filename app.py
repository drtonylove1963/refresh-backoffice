import logging
import sys
import os
from flask import Flask
from config import Config
from extensions import db, mail, csrf, login_manager
from services.breeze_service import BreezeAPI
from routes.member_routes import member_bp

def create_app():
    # Setup enhanced logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log')
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting application initialization")

    # Verify environment variables
    required_vars = ['DATABASE_URL', 'BREEZE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        if 'BREEZE_API_KEY' in missing_vars:
            logger.warning("BREEZE_API_KEY is required for member synchronization")

    # Initialize Flask app
    app = Flask(__name__)
    app.static_folder = 'static'
    app.static_url_path = '/static'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching during development
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config.from_object(Config)

    # Configure SQLAlchemy
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'prefer'}
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    with app.app_context():
        # Import and register all blueprints
        from routes import blueprints
        for blueprint in blueprints:
            url_prefix = None
            if blueprint.name == 'admin':
                url_prefix = '/admin'
            elif blueprint.name == 'member':
                url_prefix = '/member'
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            app.logger.info(f"Registered blueprint: {blueprint.name} with prefix: {url_prefix}")

        # Make csrf token available in all templates
        from flask_wtf.csrf import generate_csrf
        @app.context_processor
        def inject_csrf_token():
            return dict(csrf_token=generate_csrf())

        # Create all database tables
        db.create_all()

        # User loader for Flask-Login
        @login_manager.user_loader
        def load_user(user_id):
            from models import Admin
            return Admin.query.get(int(user_id))

    # Remove SERVER_NAME as it can cause routing issues
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
