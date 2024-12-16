import logging
from flask import render_template, request, jsonify, session, redirect, url_for, flash, current_app, render_template_string
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime, date
from models import Admin, Visitor, EmailTemplate, Member
from forms import LoginForm
from extensions import db
from services.breeze_service import BreezeAPI
from . import admin_bp
from sqlalchemy import text, inspect

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    form = LoginForm()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin.dashboard'))
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
    current_month = today.month
    
    # Get visitors data
    visitors = Visitor.query.order_by(Visitor.created_at.desc()).all()
    upcoming_visits = sum(1 for v in visitors if v.visit_date >= today)
    
    # Calculate visitor statistics
    total_visitors_this_year = sum(1 for v in visitors if v.visit_date.year == current_year)
    total_visitors_this_month = sum(1 for v in visitors if v.visit_date.year == current_year and v.visit_date.month == current_month)
    planned_visits_this_month = sum(1 for v in visitors if v.visit_date >= today and v.visit_date.month == current_month)
    
    # Get total members from database
    total_members = Member.query.count()
    
    # Initialize Breeze API client (will implement in services/breeze_service.py)
    try:
        breeze = BreezeAPI()
        
        # Fetch membership data from Breeze
        baptisms_current_year = breeze.get_baptisms_for_year(current_year)
        new_members_current_year = breeze.get_new_members_for_year(current_year)
        
    except Exception as e:
        logging.error(f"Error fetching Breeze data: {str(e)}")
        # Provide default values if Breeze API fails
        baptisms_current_year = 0
        new_members_current_year = 0
    
    return render_template('admin/dashboard.html', 
                         visitors=visitors,
                         upcoming_visits=upcoming_visits,
                         today=datetime.now(),
                         current_year=current_year,
                         total_members=total_members,
                         baptisms_current_year=baptisms_current_year,
                         new_members_current_year=new_members_current_year,
                         total_visitors_this_year=total_visitors_this_year,
                         total_visitors_this_month=total_visitors_this_month,
                         planned_visits_this_month=planned_visits_this_month)

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

@admin_bp.route('/members')
@login_required
def members():
    members = Member.query.order_by(Member.last_name, Member.first_name).all()
    for member in members:
        if member.is_active:
            member.status = 'active'
        else:
            member.status = 'inactive'
    return render_template('member/list.html', 
                         members=members, 
                         total_members=len(members),
                         is_admin=True)

@admin_bp.route('/members/<int:id>')
@login_required
def member_detail(id):
    member = Member.query.get_or_404(id)
    return render_template('member/detail.html', member=member)

@admin_bp.route('/members/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        member.first_name = request.form.get('first_name')
        member.last_name = request.form.get('last_name')
        member.email = request.form.get('email')
        member.phone = request.form.get('phone')
        member.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Member updated successfully.', 'success')
        return redirect(url_for('admin.member_detail', id=member.id))
    return render_template('member/edit.html', member=member)

@admin_bp.route('/members/sync', methods=['POST'])
@login_required
def sync_members():
    try:
        breeze = BreezeAPI()
        members = breeze.get_people()  # Using get_people instead of get_members to get detailed data
        
        for member_data in members:
            # Process each member
            member = Member.query.filter_by(breeze_id=member_data['id']).first()
            if not member:
                member = Member(
                    breeze_id=member_data['id'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            # Update basic member data
            member.first_name = member_data.get('first_name', '')
            member.last_name = member_data.get('last_name', '')
            member.email = member_data.get('email', '')
            member.phone = member_data.get('phone', '')
            member.is_active = member_data.get('status', '').lower() == 'active'
            member.profile_image = member_data.get('photo_url', '')
            member.updated_at = datetime.utcnow()
            
            # Update detailed member data
            member.gender = member_data.get('gender', '')
            member.marital_status = member_data.get('marital_status', '')
            member.address = member_data.get('address', '')
            member.grade = member_data.get('grade', '')
            member.employer = member_data.get('employer', '')
            member.church_status = member_data.get('church_status', '')
            
            # Update dates if available
            if member_data.get('baptism_date'):
                try:
                    member.baptism_date = datetime.strptime(member_data['baptism_date'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
                    
            if member_data.get('membership_date'):
                try:
                    member.membership_date = datetime.strptime(member_data['membership_date'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            
            # Update Vision Builders data
            member.vb_viewed_intro_date = member_data.get('vb_viewed_intro_date')
            member.vb_session1_date = member_data.get('vb_session1_date')
            member.vb_session2_date = member_data.get('vb_session2_date')
            member.vb_session3_date = member_data.get('vb_session3_date')
            
            # Update family relationships if available
            if member_data.get('family'):
                member.family_members = member_data['family']
            
            db.session.add(member)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Successfully synced {len(members)} members'})
    except Exception as e:
        logging.error(f"Error syncing members: {str(e)}")
        db.session.rollback()
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

@admin_bp.route('/database')
@login_required
def database():
    valid_tables = ['admins', 'members', 'visitor', 'child', 'email_template']
    inspector = inspect(db.engine)
    table_info = []
    
    for table_name in inspector.get_table_names():
        if table_name.lower() in valid_tables:
            count = db.session.execute(text(f'SELECT COUNT(*) FROM {table_name}')).scalar()
            columns = inspector.get_columns(table_name)
            
            table_info.append({
                'name': table_name,
                'record_count': count,
                'columns': len(columns)
            })
    
    return render_template('admin/database.html', tables=table_info)

@admin_bp.route('/api/table-schema/<table_name>')
@login_required
def get_table_schema(table_name):
    valid_tables = ['admins', 'members', 'visitor', 'child', 'email_template']
    try:
        if table_name.lower() not in valid_tables:
            return jsonify({
                'success': False,
                'error': f'Table {table_name} is not accessible'
            }), 403
            
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            return jsonify({
                'success': False,
                'error': 'Table not found'
            }), 404
            
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column.get('nullable', True),
                'default': str(column.get('default', ''))
            })
            
        return jsonify({
            'success': True,
            'schema': {
                'table_name': table_name,
                'columns': columns
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@admin_bp.route('/api/table-data/<table_name>')
@login_required
def get_table_data(table_name):
    valid_tables = ['admins', 'members', 'visitor', 'child', 'email_template']
    try:
        print(f"Fetching data for table: {table_name}")  # Debug log
        
        if table_name.lower() not in valid_tables:
            print(f"Table {table_name} not in valid_tables: {valid_tables}")  # Debug log
            return jsonify({
                'success': False,
                'error': f'Table {table_name} is not accessible'
            }), 403
            
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            print(f"Table {table_name} not found in database")  # Debug log
            return jsonify({
                'success': False,
                'error': 'Table not found'
            }), 404
            
        # Get all columns for the table
        columns = [column['name'] for column in inspector.get_columns(table_name)]
        print(f"Columns found: {columns}")  # Debug log
        
        # Query the data
        query = text(f'SELECT * FROM {table_name}')
        result = db.session.execute(query)
        
        # Convert results to list of dictionaries
        data = []
        for row in result:
            item = {}
            for i, column in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, date):
                    value = value.strftime('%Y-%m-%d')
                item[column] = str(value) if value is not None else None
            data.append(item)
            
        print(f"Found {len(data)} rows")  # Debug log
        response_data = {
            'success': True,
            'data': data,
            'columns': columns  # Ensure columns is included in response
        }
        print(f"Sending response: {response_data}")  # Debug log
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in get_table_data: {str(e)}")  # Debug log
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@admin_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    # Check if any admin exists
    if Admin.query.first() is not None:
        flash('Admin account already exists.', 'warning')
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username and password:
            admin = Admin(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            flash('Admin account created successfully!', 'success')
            return redirect(url_for('admin.login'))
        
        flash('Username and password are required.', 'danger')
    
    return render_template('admin/setup.html')