import os
import logging
from app import create_app, db
from src.models.visitor import Child, Visitor
from src.models.breeze_profile import BreezeProfile
from src.services.breeze_service import BreezeAPI

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def main():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Initialize Breeze API
        breeze = BreezeAPI()
        
        # Sync profile fields
        logger.info("Starting profile fields sync...")
        stats = breeze.sync_profile_fields(db, BreezeProfile)
        logger.info(f"Sync complete. Stats: {stats}")
        
        # Print all profile fields
        profiles = BreezeProfile.query.all()
        logger.info(f"\nTotal profile fields: {len(profiles)}")
        for profile in profiles:
            logger.info(f"Field: {profile.name} -> {profile.local_field_name}")

if __name__ == '__main__':
    main()
