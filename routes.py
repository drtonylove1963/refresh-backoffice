import logging
import time
from functools import wraps
from flask import render_template, request, jsonify, session, redirect, url_for, flash, render_template_string, current_app
from flask_wtf.csrf import CSRFError
from app import db
from models import Visitor, Child, Admin, EmailTemplate
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from typing import Optional, List, Dict, Any

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def get_sendgrid_client():
    return SendGridAPIClient(api_key=current_app.config['SENDGRID_API_KEY'])

# Form routes
from flask import Blueprint

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('visit_form.html')

@main_bp.route('/save_step', methods=['POST'])
def save_step():
    data = request.get_json()
    step = data.get('step')
    
    if not step:
        return jsonify({'status': 'error', 'message': 'Step number is required'})
    
    # Only update session if data has changed
    current_data = session.get(f'step_{step}')
    if current_data != data:
        session[f'step_{step}'] = data
    return jsonify({'status': 'success'})

@main_bp.route('/submit', methods=['POST'])
def submit_form():
    logging.debug("Form submission started")
    logging.debug(f"Session data: {session}")
    
    try:
        # Validate all required steps are present
        required_steps = ['step_1', 'step_2', 'step_3', 'step_5']  # step_4 (children) is optional
        missing_steps = [step for step in required_steps if step not in session]
        
        if missing_steps:
            raise ValueError(f"Missing required information from steps: {', '.join(missing_steps)}")
        
        # Extract visitor data from session
        visitor_data = {
            'first_name': session['step_1'].get('firstName'),
            'last_name': session['step_1'].get('lastName'),
            'phone': session['step_2'].get('phone'),
            'email': session['step_3'].get('email'),
            'visit_date': datetime.strptime(session['step_5'].get('visitDate'), '%Y-%m-%d').date()
        }
        
        # Validate required fields
        missing_fields = [field for field, value in visitor_data.items() if not value]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Create visitor record
        visitor = Visitor(**visitor_data)
        logging.debug("Created visitor object")
        
        # Add any children if present
        if 'step_4' in session and session.get('step_4', {}).get('children'):
            for child_data in session['step_4']['children']:
                # Only add child if all required fields are present
                if all(child_data.get(field) for field in ['firstName', 'lastName', 'dob']):
                    child = Child(
                        first_name=child_data['firstName'],
                        last_name=child_data['lastName'],
                        date_of_birth=datetime.strptime(child_data['dob'], '%Y-%m-%d').date(),
                        special_instructions=child_data.get('specialInstructions', '')
                    )
                    visitor.children.append(child)
                    logging.debug(f"Added child: {child.first_name} {child.last_name}")
        
        # Save to database
        try:
            db.session.add(visitor)
            db.session.commit()
            logging.debug("Database commit successful")
            
            # Send notifications
            send_staff_notification(visitor)
            logging.debug("Staff notification sent")
            send_visitor_confirmation(visitor)
            logging.debug("Visitor confirmation sent")
            
            # Batch clear session data
            session_keys = [key for key in session if key.startswith('step_')]
            for key in session_keys:
                session.pop(key)
            
            return jsonify({
                'status': 'success',
                'message': 'Thank you for registering! You will receive a confirmation email shortly.'
            })
            
        except Exception as db_error:
            db.session.rollback()
            logging.error(f"Database error: {str(db_error)}")
            raise ValueError("Failed to save registration. Please try again.")
            
    except ValueError as e:
        logging.error(f"Validation error in form submission: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logging.error(f"Unexpected error in form submission: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again or contact support.',
            'error_details': str(e) if app.debug else None
        }), 500

def send_staff_notification(visitor: Visitor) -> bool:
    """Send notification to staff about new visitor registration."""
    try:
        send_email(
            subject='New Visit Registration',
            to_email=app.config['STAFF_EMAIL'],
            template_name='staff_notification',
            template_data={'visitor': visitor, 'config': app.config}
        )
        return True
    except Exception as e:
        logging.error(f"Failed to send staff notification: {str(e)}")
        # Don't raise the error, just return False to indicate failure
        return False

def send_visitor_confirmation(visitor: Visitor) -> bool:
    """Send confirmation email to visitor."""
    try:
        send_email(
            subject='Welcome to Refresh Church!',
            to_email=visitor.email,
            template_name='visitor_confirmation',
            template_data={'visitor': visitor, 'config': app.config}
        )
        return True
    except Exception as e:
        logging.error(f"Failed to send visitor confirmation: {str(e)}")
        # Don't raise the error, just return False to indicate failure
        return False

def send_email(subject: str, to_email: str, template_name: str, template_data: dict, max_retries: int = 3) -> None:
    """Send an email using SendGrid with retry logic and improved error handling."""
    if not to_email or '@' not in to_email:
        logging.error(f"Invalid email address: {to_email}")
        raise ValueError("Invalid email address")

    if not app.config.get('SENDGRID_API_KEY'):
        logging.error("SendGrid API key is not configured")
        raise ValueError("SendGrid API key is not configured")

    try:
        # Try to get custom template from database
        custom_template = EmailTemplate.query.filter_by(template_type=template_name).first()
        
        if custom_template:
            # Use custom template
            html_content = render_template_string(custom_template.html_content, **template_data)
            email_subject = custom_template.subject
        else:
            # Fall back to default template
            html_content = render_template(f'email/{template_name}.html', **template_data)
            email_subject = subject
        
        message = Mail(
            from_email=Email(app.config.get('MAIL_DEFAULT_SENDER', app.config.get('SENDGRID_VERIFIED_SENDER'))),
            to_emails=To(to_email),
            subject=email_subject,
            html_content=HtmlContent(html_content)
        )

        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                response = sg.send(message)
                if response.status_code in [200, 201, 202]:
                    logging.info(f"Email sent successfully to {to_email}. Status code: {response.status_code}")
                    return
                else:
                    raise Exception(f"SendGrid API returned status code: {response.status_code}")
            except Exception as e:
                last_error = e
                retry_count += 1
                logging.warning(f"Email sending attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
        
        # If we've exhausted all retries, log and raise the last error
        error_msg = f"Failed to send email after {max_retries} attempts"
        logging.error(f"{error_msg}. Last error: {str(last_error)}")
        return False
        
    except Exception as e:
        logging.error(f"Email preparation failed: {str(e)}")
        return False

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    from datetime import date, datetime
    today = date.today()
    visitors = Visitor.query.order_by(Visitor.created_at.desc()).all()
    upcoming_visits = sum(1 for v in visitors if v.visit_date.date() >= today)
    return render_template('admin/dashboard.html', 
                         visitors=visitors,
                         upcoming_visits=upcoming_visits)

@app.route('/admin/visitor/<int:visitor_id>')
@admin_required
def get_visitor_details(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    return jsonify({
        'first_name': visitor.first_name,
        'last_name': visitor.last_name,
        'email': visitor.email,
        'phone': visitor.phone,
        'visit_date': visitor.visit_date.strftime('%Y-%m-%d'),
        'children': [{
            'first_name': child.first_name,
            'last_name': child.last_name,
            'date_of_birth': child.date_of_birth.strftime('%Y-%m-%d'),
            'special_instructions': child.special_instructions
        } for child in visitor.children]
    })

@app.route('/admin/visitor/<int:visitor_id>/delete', methods=['POST'])
@admin_required
def delete_visitor(visitor_id):
    try:
        visitor = Visitor.query.get_or_404(visitor_id)
        logging.info(f"Deleting visitor registration for {visitor.full_name}")
        db.session.delete(visitor)
        db.session.commit()
        flash('Visitor registration deleted successfully.', 'success')
        logging.info(f"Successfully deleted visitor registration for {visitor.full_name}")
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error deleting visitor {visitor_id}: {str(e)}"
        logging.error(error_msg)
        flash('Error deleting visitor registration. Please try again.', 'danger')
    
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/templates')
@admin_required
def email_templates():
    templates = EmailTemplate.query.all()
    return render_template('admin/templates.html', templates=templates)

@app.route('/admin/templates/<template_type>/edit', methods=['GET', 'POST'])
@admin_required
def edit_template(template_type):
    template = EmailTemplate.query.filter_by(template_type=template_type).first()
    
    if request.method == 'POST':
        if not template:
            template = EmailTemplate(template_type=template_type)
        
        template.subject = request.form['subject']
        template.html_content = request.form['html_content']
        
        try:
            db.session.add(template)
            db.session.commit()
            flash('Template updated successfully!', 'success')
            return redirect(url_for('email_templates'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating template. Please try again.', 'danger')
            logging.error(f"Template update error: {str(e)}")
    
    if not template:
        # Load default template if no custom template exists
        defaults = EmailTemplate.get_default_templates()
        default_template = defaults.get(template_type, {})
        template = EmailTemplate(
            template_type=template_type,
            subject=default_template.get('subject', ''),
            html_content=default_template.get('html_content', '')
        )
    
    return render_template('admin/edit_template.html', template=template)

@app.route('/admin/templates/preview', methods=['POST'])
@admin_required
def preview_template():
    try:
        html_content = request.form['html_content']
        # Use cached mock data for preview
        mock_data = getattr(preview_template, '_mock_data', None)
        if not mock_data:
            mock_data = type('MockVisitor', (), {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'phone': '(555) 123-4567',
                'visit_date': datetime.now(),
                'children': []
            })
            setattr(preview_template, '_mock_data', mock_data)
        
        rendered_html = render_template_string(
            html_content,
            visitor=mock_data,
            config=app.config
        )
        return jsonify({'html': rendered_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logging.error(f"CSRF Error occurred: {str(e)}")
    flash('Your session has expired. Please try the action again.', 'warning')
    return redirect(request.referrer or url_for('admin_dashboard'))