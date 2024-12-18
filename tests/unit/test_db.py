from app import create_app
from src.lib.extensions import db
from src.models import BreezeProfile
import os

os.environ['DATABASE_URL'] = 'sqlite:///./app.db'
os.environ['SECRET_KEY'] = 'dev-key'

app = create_app()

with app.app_context():
    # Create a test profile
    test_profile = BreezeProfile(
        breeze_field_id="test_field_1",
        profile_section_id="main",
        field_type="text",
        name="Test Field",
        position=1,
        profile_id="profile1",
        local_field_name="first_name"
    )
    
    # Add and commit
    db.session.add(test_profile)
    db.session.commit()
    
    # Query and print
    profiles = BreezeProfile.query.all()
    print(f"\nNumber of profiles: {len(profiles)}")
    for profile in profiles:
        print(f"\nProfile ID: {profile.id}")
        print(f"Breeze Field ID: {profile.breeze_field_id}")
        print(f"Name: {profile.name}")
        print(f"Local Field Name: {profile.local_field_name}")
