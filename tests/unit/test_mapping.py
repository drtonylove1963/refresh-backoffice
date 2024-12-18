import os
from src.services.breeze_service import BreezeAPI
from src.models.breeze_profile import BreezeProfile
from src.models.admin import Admin
from src.lib.extensions import db
from app import create_app

def setup_test_database(db):
    # Create an admin user
    admin = Admin(username='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create sample profile field mappings
    fields = [
        BreezeProfile(
            breeze_field_id='53794215',
            field_type='dropdown',
            name='Gender',
            local_field_name='gender'
        ),
        BreezeProfile(
            breeze_field_id='1114613888',
            field_type='dropdown',
            name='Marital Status',
            local_field_name='marital_status'
        ),
        BreezeProfile(
            breeze_field_id='1776400450',
            field_type='dropdown',
            name='Church Status',
            local_field_name='church_status'
        ),
        BreezeProfile(
            breeze_field_id='1733583868',
            field_type='phone',
            name='Phone Numbers',
            local_field_name='phone'
        ),
        BreezeProfile(
            breeze_field_id='1866721325',
            field_type='email',
            name='Email Addresses',
            local_field_name='email'
        )
    ]
    
    for field in fields:
        db.session.add(field)
    db.session.commit()

def test_mapping():
    # Set up test database
    os.environ['DATABASE_URL'] = 'sqlite:///test.db'
    os.environ['BREEZE_API_KEY'] = 'your-api-key-here'  # Replace with actual key
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    breeze = BreezeAPI()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Set up test data
        setup_test_database(db)
        
        # Test the mappings
        profile_fields = BreezeProfile.query.all()
        print('Profile Fields Mapping:\n')
        for field in profile_fields:
            print(f'{field.breeze_field_id} -> {field.local_field_name}')
        
        print('\nMapped Member Data:\n')
        mapped_data = breeze.get_member_details('48075044', profile_fields)
        print(mapped_data)
        
        # Clean up
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    test_mapping()
