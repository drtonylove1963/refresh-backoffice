from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_user, logout_user, login_required, current_user
from src.models import Member, Admin
from src.core.extensions import db
from src.services.breeze_service import BreezeAPI
from src.forms.auth import LoginForm
from src.forms.member import MemberForm
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash
from datetime import datetime
import os

def register_template_filters(app):
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        return value.strftime('%Y-%m-%d %H:%M:%S')

# Create blueprints
main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')
auth = Blueprint('auth', __name__, url_prefix='/auth')

# Main routes
@main.route('/')
def index():
    """Home page."""
    return render_template('main/index.html')

@main.route('/visit-form')
def visit_form():
    """Visit form page."""
    return render_template('main/visit_form.html')

# Admin routes
@admin.route('/')
@login_required
def dashboard():
    """Admin dashboard home."""
    return render_template('admin/dashboard.html')

@admin.route('/members')
@login_required
def members():
    """Display all members from the database."""
    try:
        members_list = Member.query.order_by(Member.last_name, Member.first_name).all()
        return render_template('admin/members.html', members=members_list)
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error while fetching members: {str(e)}")
        db.session.rollback()
        flash('Error loading members. Please try again later.', 'danger')
        return render_template('admin/members.html', members=[])

@admin.route('/members/sync', methods=['POST'])
@login_required
def sync_members():
    """Sync members with Breeze API."""
    try:
        breeze = BreezeAPI()
        members_data = breeze.get_members()
        
        # Create profile images directory if it doesn't exist
        profile_images_dir = os.path.join(current_app.static_folder, 'profile_images')
        os.makedirs(profile_images_dir, exist_ok=True)
        
        for member_data in members_data:
            # Get profile image path from Breeze data
            profile_path = member_data.get('details', {}).get('path')
            
            # Download profile image if available
            local_image_path = None
            if profile_path:
                local_image_path = breeze.download_profile_image(profile_path, profile_images_dir)
                if local_image_path:
                    # Convert absolute path to URL path relative to static folder
                    local_image_path = f"/static/profile_images/{os.path.basename(local_image_path)}"
            
            # Update member data with local image path
            member_dict = Member.from_breeze_data(member_data)
            member_dict['profile_image'] = local_image_path
            
            existing_member = Member.query.filter_by(breeze_id=member_dict['breeze_id']).first()
            
            if existing_member:
                # Update existing member
                for key, value in member_dict.items():
                    setattr(existing_member, key, value)
            else:
                # Create new member
                new_member = Member(**member_dict)
                db.session.add(new_member)
        
        db.session.commit()
        flash(f'Successfully synced {len(members_data)} members from Breeze.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error syncing members with Breeze: {str(e)}")
        db.session.rollback()
        flash('Error syncing members with Breeze. Please try again later.', 'danger')
    
    return redirect(url_for('admin.members'))

@admin.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    """Add a new member."""
    form = MemberForm()
    if form.validate_on_submit():
        member = Member(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            is_active=form.is_active.data,
            church_status=form.church_status.data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(member)
        db.session.commit()
        flash('Member added successfully.', 'success')
        return redirect(url_for('admin.members'))
    return render_template('admin/add_member.html', form=form)

@admin.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    """Edit an existing member."""
    member = Member.query.get_or_404(member_id)
    form = MemberForm(obj=member)
    
    if form.validate_on_submit():
        member.first_name = form.first_name.data
        member.last_name = form.last_name.data
        member.email = form.email.data
        member.phone = form.phone.data
        member.is_active = form.is_active.data
        member.church_status = form.church_status.data
        member.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Member updated successfully.', 'success')
        return redirect(url_for('admin.members'))
        
    return render_template('admin/edit_member.html', form=form, member=member)

@admin.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
def delete_member(member_id):
    """Delete a member."""
    member = Member.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully.', 'success')
    return redirect(url_for('admin.members'))

@admin.route('/visits')
@login_required
def visits():
    """Display all visits."""
    return render_template('admin/visits.html')

@admin.route('/email-templates')
@login_required
def email_templates():
    """Display and manage email templates."""
    try:
        # You might want to fetch email templates from your database here
        return render_template('admin/email_templates.html')
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error while fetching email templates: {str(e)}")
        flash('Error loading email templates. Please try again later.', 'danger')
        return render_template('admin/email_templates.html')

# Auth routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and check_password_hash(admin.password_hash, form.password.data):
            login_user(admin, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# List of all blueprints to register
blueprints = [main, admin, auth]
