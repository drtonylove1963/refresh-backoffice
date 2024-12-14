import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('SENDGRID_VERIFIED_SENDER')
    
    # Church information
    STAFF_EMAIL = 'drtony_love@refresh-church.com'
    CHURCH_PHONE = '(816) 761-5161'
    CHURCH_ADDRESS = '10021 Bannister Road, Kansas City, MO 64134'
    SERVICE_TIME = '10:00 AM'
    CHURCH_WEBSITE = 'www.refreshkc.com'
