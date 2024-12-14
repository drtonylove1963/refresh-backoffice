import logging
from flask import render_template, request, jsonify, session, redirect, url_for, flash, current_app, render_template_string
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime, date
from models import Admin, Visitor, EmailTemplate, Member
from forms import LoginForm
from extensions import db
from services.breeze_service import BreezeAPI
from . import admin_bp

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/planned-visits')
@login_required
def planned_visits():
    visitors = Visitor.query.order_by(Visitor.created_at.desc()).all()
    return render_template('admin/planned_visits.html', visitors=visitors)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    current_year = today.year
    
    # Get visitors data
    visitors = Visitor.query.order_by(Visitor.created_at.desc()).all()
    upcoming_visits = sum(1 for v in visitors if v.visit_date >= today)
    
    # Initialize Breeze API client (will implement in services/breeze_service.py)
    try:
        breeze = BreezeAPI()
        
        # Fetch membership data from Breeze
        membership_total = breeze.get_total_membership()
        baptisms_current_year = breeze.get_baptisms_for_year(current_year)
        new_members_current_year = breeze.get_new_members_for_year(current_year)
        
    except Exception as e:
        logging.error(f"Error fetching Breeze data: {str(e)}")
        # Provide default values if Breeze API fails
        membership_total = 0
        baptisms_current_year = 0
        new_members_current_year = 0
    
    return render_template('admin/dashboard.html', 
                         visitors=visitors,
                         upcoming_visits=upcoming_visits,
                         today=datetime.now(),
                         current_year=current_year,
                         membership_total=membership_total,
                         baptisms_current_year=baptisms_current_year,
                         new_members_current_year=new_members_current_year)

@admin_bp.route('/visitor/<int:visitor_id>')
@login_required
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

@admin_bp.route('/visitor/<int:visitor_id>/delete', methods=['POST'])
@login_required
def delete_visitor(visitor_id):
    try:
        visitor = Visitor.query.get_or_404(visitor_id)
        db.session.delete(visitor)
        db.session.commit()
        flash('Visitor registration deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting visitor registration.', 'danger')
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/templates')
@login_required
def email_templates():
    templates = EmailTemplate.query.all()
    return render_template('admin/templates.html', templates=templates)

@admin_bp.route('/templates/<template_type>/edit', methods=['GET', 'POST'])
@login_required
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
            return redirect(url_for('admin.email_templates'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating template. Please try again.', 'danger')
            logging.error(f"Template update error: {str(e)}")
    
    if not template:
        defaults = EmailTemplate.get_default_templates()
        default_template = defaults.get(template_type, {})
        template = EmailTemplate(
            template_type=template_type,
            subject=default_template.get('subject', ''),
            html_content=default_template.get('html_content', '')
        )
    
    return render_template('admin/edit_template.html', template=template)

@admin_bp.route('/templates/preview', methods=['POST'])
@login_required
def preview_template():
    try:
        html_content = request.form['html_content']
        mock_visitor = type('MockVisitor', (), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '(555) 123-4567',
            'visit_date': datetime.now(),
            'children': []
        })
        
        rendered_html = render_template_string(
            html_content,
            visitor=mock_visitor,
            config=current_app.config
        )
        return jsonify({'html': rendered_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/test')
@admin_bp.route('/test/')
@login_required
def test_page():
    """Test page to display Breeze API member data"""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Loading test page with member data")
        members = Member.query.filter_by(is_active=True).order_by(Member.first_name).all()
        if not members:
            logger.warning("No active members found in database")
            flash('No active members found. Please add some members first.', 'warning')
        return render_template('admin/test.html', members=members)
    except Exception as e:
        logger.error(f"Error loading test page: {str(e)}", exc_info=True)
        flash('Error loading test page. Please check the logs for details.', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/breeze-data/<breeze_id>')
@login_required
def get_breeze_data(breeze_id):
    """Fetch member data from Breeze API"""
    try:
        from utils.cache import cache_api_response
        
        @cache_api_response(expiry_minutes=15)
        def fetch_member_data(member_id):
            breeze = BreezeAPI()
            return breeze.get_person(member_id)
        
        member_data = fetch_member_data(breeze_id)
        return jsonify(member_data)
    except Exception as e:
        logging.error(f"Error fetching Breeze data: {str(e)}")
        return jsonify({'error': str(e)}), 500
@admin_bp.route('/breeze-profile-fields')
@login_required
def get_breeze_profile_fields():
    """Fetch profile fields from Breeze API"""
    logger = logging.getLogger(__name__)
    try:
        from utils.cache import cache_api_response
        
        @cache_api_response(expiry_minutes=30)
        def fetch_profile_fields():
            breeze = BreezeAPI()
            return breeze.get_profile_fields()
        
        logger.info("Attempting to fetch Breeze profile fields")
        profile_fields = fetch_profile_fields()
        logger.info(f"Successfully retrieved {len(profile_fields) if isinstance(profile_fields, list) else 1} profile fields")
        return jsonify(profile_fields)
        
    except ValueError as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({
            'error': 'API Error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in profile fields endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Server Error',
            'message': 'An unexpected error occurred while fetching profile fields'
        }), 500