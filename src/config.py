import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.flaskenv'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    
    # Breeze API settings
    BREEZE_API_KEY = os.environ.get('BREEZE_API_KEY')
    BREEZE_API_URL = 'https://api.breezechms.com'
    
    # Application settings
    VISIT_FORM_RECIPIENTS = os.environ.get('VISIT_FORM_RECIPIENTS', '').split(',')
    CHURCH_NAME = os.environ.get('CHURCH_NAME', 'Refresh Church')
    CHURCH_ADDRESS = os.environ.get('CHURCH_ADDRESS', '123 Main St, City, ST 12345')
    CHURCH_PHONE = os.environ.get('CHURCH_PHONE', '(123) 456-7890')
    CHURCH_EMAIL = os.environ.get('CHURCH_EMAIL', 'info@refreshchurch.org')
