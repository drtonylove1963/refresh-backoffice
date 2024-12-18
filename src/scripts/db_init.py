from src import create_app
from src.models import db

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
