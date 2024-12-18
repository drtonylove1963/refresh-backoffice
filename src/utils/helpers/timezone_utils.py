from datetime import datetime
import pytz

def format_datetime(dt):
    """Format datetime to string with timezone"""
    if not dt:
        return None
    if not dt.tzinfo:
        dt = pytz.UTC.localize(dt)
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')

def format_date(dt):
    """Format date to string"""
    if not dt:
        return None
    return dt.strftime('%Y-%m-%d')
