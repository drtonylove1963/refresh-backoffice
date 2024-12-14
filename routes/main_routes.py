from flask import render_template, request, jsonify, session, current_app, redirect, url_for
from models import Visitor, Child
from extensions import db
import logging
from datetime import datetime
from services.email_service import send_staff_notification, send_visitor_confirmation
from . import main_bp

@main_bp.route('/')
def index():
    return redirect(url_for('admin.login'))

@main_bp.route('/visit')
def visit_form():
    return render_template('visit_form.html')

@main_bp.route('/save_step', methods=['POST'])
def save_step():
    data = request.get_json()
    step = data.get('step')
    
    if not step:
        return jsonify({'status': 'error', 'message': 'Step number is required'})
    
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
            
            # Clear session data
            for key in list(session.keys()):
                if key.startswith('step_'):
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
            'error_details': str(e) if current_app.debug else None
        }), 500
