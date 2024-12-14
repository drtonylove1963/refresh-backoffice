from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from models.member import Member, Role
from services.breeze_service import BreezeAPI
from app import db
from functools import wraps
import logging

member_bp = Blueprint('member', __name__)
breeze_service = BreezeAPI()

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.role == Role.ADMIN:
            flash('You must be an admin to access this page.', 'error')
            return redirect(url_for('member.member_list'))
        return f(*args, **kwargs)
    return decorated_function

@member_bp.route('/')
@member_bp.route('/list')
@login_required
def list():
    """List all members - accessible to all authenticated users"""
    if not current_user.is_authenticated:
        flash('Please log in to view members.', 'warning')
        return redirect(url_for('admin.login'))
    
    members = Member.query.filter_by(is_active=True).all()
    total_members = len(members)
    is_admin = current_user.role == Role.ADMIN
    return render_template(
        'members/list.html',
        members=members,
        total_members=total_members,
        is_admin=is_admin
    )

@member_bp.route('/members/sync', methods=['POST'])
@admin_required
def sync_members():
    """Sync members with BreezeChMS - admin only"""
    try:
        stats = breeze_service.sync_members(db, Member)
        flash(f"Sync completed: {stats['created']} created, {stats['updated']} updated, {stats['errors']} errors", 'success')
    except Exception as e:
        logging.error(f"Sync error: {str(e)}")
        flash('Error syncing members with BreezeChMS', 'error')
    
    return redirect(url_for('member.member_list'))

@member_bp.route('/<int:id>')
def member_detail(id):
    """View member details - accessible to all authenticated users"""
    member = Member.query.get_or_404(id)
    is_admin = current_user.is_authenticated and current_user.role == Role.ADMIN
    return render_template(
        'members/detail.html',
        member=member,
        is_admin=is_admin
    )

@member_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_member(id):
    """Edit member details - admin only"""
    member = Member.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update local database
            member.first_name = request.form['first_name']
            member.last_name = request.form['last_name']
            member.email = request.form['email']
            member.phone = request.form['phone']
            
            # Update BreezeChMS
            breeze_data = {
                'first_name': member.first_name,
                'last_name': member.last_name,
                'email': member.email,
                'phone': member.phone
            }
            breeze_service.update_person(member.breeze_id, breeze_data)
            
            db.session.commit()
            flash('Member updated successfully', 'success')
            return redirect(url_for('member.member_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Update error: {str(e)}")
            flash('Error updating member', 'error')
    
    return render_template('members/edit.html', member=member)
