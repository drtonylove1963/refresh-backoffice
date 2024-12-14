import sys
from app import create_app, db
from models import Admin, Role

def create_admin_user(username, password):
    app = create_app()
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:
                print(f"Admin user '{username}' already exists")
                return False
            
            # Create new admin user with ADMIN role
            admin = Admin(username=username, role=Role.ADMIN)
            admin.set_password(password)
            
            # Add and commit to database
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{username}' created successfully")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    create_admin_user(username, password)
