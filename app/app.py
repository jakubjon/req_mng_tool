from flask import request, jsonify, send_file, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
import uuid
from dotenv import load_dotenv
from . import create_app
from app import db
from app.models import Requirement, CellHistory, Group, User, Project


# Load environment variables
app = create_app()

# Load environment variables for this module as well
load_dotenv()

def get_current_user():
    """Get current user from session"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return user.username if user else None
    return None

def login_required(f):
    """Decorator to require login for routes"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Utility function to check if any users exist

def users_exist():
    return User.query.first() is not None

def check_project_access(user_id, project_id):
    """Helper function to check if user has access to a project"""
    user = User.query.get(user_id)
    project = Project.query.get(project_id)
    
    if not user or not project:
        return False, None, None
    
    return user in project.users, user, project

# Web Routes
@app.route('/')
def index():
    """Serve the main application interface"""
    # If no users exist, redirect to login for registration
    if not users_exist():
        return redirect(url_for('login_page'))
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    # Defensive: check if user_id is valid
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    # If no users exist, allow registration
    if not users_exist():
        return render_template('login.html')
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return redirect(url_for('index'))
        else:
            session.pop('user_id', None)
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.pop('user_id', None)
    return jsonify({'success': True, 'message': 'Logout successful'})

@app.route('/api/register', methods=['POST'])
def register():
    """Handle user registration"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '').strip()  # Get email and remove whitespace
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Convert empty email to None to avoid unique constraint violations
        if not email:
            email = None
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        if email and User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/current')
def get_current_user_info():
    """Get current user information"""
    if not users_exist():
        return jsonify({'success': False, 'error': 'No users exist'}), 401
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return jsonify({'success': False, 'error': 'User not found'}), 401
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

# Project Management APIs
@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    """Get all projects accessible to current user"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 401
        
        # Get projects the user has access to
        projects = user.projects
        
        return jsonify({
            'success': True,
            'data': [project.to_dict() for project in projects]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    try:
        data = request.json
        current_user = get_current_user()
        user = User.query.get(session['user_id'])
        
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Project name is required'}), 400
        
        # Check if project name already exists
        existing_project = Project.query.filter_by(name=data['name']).first()
        if existing_project:
            return jsonify({'success': False, 'error': 'Project name already exists'}), 400
        
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            created_by=current_user
        )
        
        # Add current user to project access
        project.users.append(user)
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'data': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update a project"""
    try:
        user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.json
        
        if 'name' in data:
            # Check if new name conflicts with existing project
            existing_project = Project.query.filter_by(name=data['name']).first()
            if existing_project and existing_project.id != project_id:
                return jsonify({'success': False, 'error': 'Project name already exists'}), 400
            project.name = data['name']
        
        if 'description' in data:
            project.description = data['description']
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'data': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    try:
        user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete project (cascade will handle groups and requirements)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>/users', methods=['POST'])
@login_required
def add_user_to_project(project_id):
    """Add user access to project"""
    try:
        user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if current user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        
        target_user = User.query.filter_by(username=username).first()
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if target_user in project.users:
            return jsonify({'success': False, 'error': 'User already has access to this project'}), 400
        
        project.users.append(target_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} added to project successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<project_id>/users/<user_id>', methods=['DELETE'])
@login_required
def remove_user_from_project(project_id, user_id):
    """Remove user access from project"""
    try:
        current_user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if current user has access to this project
        if current_user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if target_user not in project.users:
            return jsonify({'success': False, 'error': 'User does not have access to this project'}), 400
        
        # Don't allow removing the last user from a project
        if len(project.users) == 1:
            return jsonify({'success': False, 'error': 'Cannot remove the last user from a project'}), 400
        
        project.users.remove(target_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {target_user.username} removed from project successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# API Routes
@app.route('/api/groups', methods=['GET'])
@login_required
def get_groups():
    """Get all groups with hierarchy for a specific project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get all groups for this project
        groups = Group.query.filter_by(project_id=project_id).all()
        
        # Build hierarchy
        def build_hierarchy(parent_id=None):
            children = [g for g in groups if g.parent_id == parent_id]
            return [{
                **g.to_dict(),
                'children': build_hierarchy(g.id)
            } for g in children]
        
        hierarchy = build_hierarchy()
        
        return jsonify({
            'success': True,
            'data': hierarchy
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/groups', methods=['POST'])
@login_required
def create_group():
    """Create a new group"""
    try:
        data = request.json
        current_user = get_current_user()
        
        if not data.get('project_id'):
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        user = User.query.get(session['user_id'])
        project = Project.query.get(data['project_id'])
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if parent group exists and belongs to the same project
        if data.get('parent_id'):
            parent_group = Group.query.get(data['parent_id'])
            if not parent_group or parent_group.project_id != data['project_id']:
                return jsonify({'success': False, 'error': 'Parent group not found or does not belong to this project'}), 400
        
        group = Group(
            name=data['name'],
            description=data.get('description', ''),
            parent_id=data.get('parent_id'),
            project_id=data['project_id']
        )
        
        db.session.add(group)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group created successfully',
            'data': group.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/groups/<group_id>', methods=['PUT'])
@login_required
def update_group(group_id):
    """Update a group"""
    try:
        user = User.query.get(session['user_id'])
        group = Group.query.get(group_id)
        
        if not group:
            return jsonify({'success': False, 'error': 'Group not found'}), 404
        
        # Check if user has access to the project this group belongs to
        project = Project.query.get(group.project_id)
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.json
        
        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'parent_id' in data:
            # Check if new parent exists and belongs to the same project
            if data['parent_id']:
                parent_group = Group.query.get(data['parent_id'])
                if not parent_group or parent_group.project_id != group.project_id:
                    return jsonify({'success': False, 'error': 'Parent group not found or does not belong to this project'}), 400
            group.parent_id = data['parent_id']
        
        group.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Group updated successfully',
            'data': group.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/groups/<group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id):
    """Delete a group"""
    try:
        user = User.query.get(session['user_id'])
        group = Group.query.get(group_id)
        
        if not group:
            return jsonify({'success': False, 'error': 'Group not found'}), 404
        
        # Check if user has access to the project this group belongs to
        project = Project.query.get(group.project_id)
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Check if group has requirements
        if group.requirements.count() > 0:
            return jsonify({'success': False, 'error': 'Cannot delete group with requirements. Please move or delete all requirements first.'}), 400
        
        # Check if group has children
        if group.children.count() > 0:
            return jsonify({'success': False, 'error': 'Cannot delete group with child groups. Please move or delete all child groups first.'}), 400
        
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Group deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements', methods=['GET'])
@login_required
def get_requirements():
    """Get all requirements with optional filtering for a specific project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        user = User.query.get(session['user_id'])
        project = Project.query.get(project_id)
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Query parameters for filtering
        status = request.args.get('status')
        chapter = request.args.get('chapter')
        group_id = request.args.get('group_id')
        parent_id = request.args.get('parent_id')
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        
        query = Requirement.query.filter_by(project_id=project_id)
        
        # Handle deleted requirements logic
        if status == 'deleted':
            # If explicitly filtering for deleted, include them
            query = query.filter(Requirement.status == 'deleted')
        elif include_deleted:
            # If show deleted checkbox is checked, include all requirements
            pass  # Don't filter out deleted
        else:
            # By default, exclude deleted requirements
            query = query.filter(Requirement.status != 'deleted')
        
        if status and status != 'deleted':
            query = query.filter(Requirement.status == status)
        if chapter:
            query = query.filter(Requirement.chapter == chapter)
        if group_id:
            # Verify group belongs to this project
            group = Group.query.get(group_id)
            if not group or group.project_id != project_id:
                return jsonify({'success': False, 'error': 'Group not found or does not belong to this project'}), 400
            query = query.filter(Requirement.group_id == group_id)
        
        requirements = query.all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict(shallow=True) for req in requirements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['GET'])
@login_required
def get_requirement(requirement_id):
    """Get a specific requirement with details (M2M children)"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], requirement.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Get history
        history = CellHistory.query.filter_by(requirement_id=requirement.id).order_by(CellHistory.changed_at.desc()).all()
        data = requirement.to_dict()
        data['history'] = [h.to_dict() for h in history]
        # children already included as M2M in to_dict
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['PUT'])
@login_required
def update_requirement(requirement_id):
    """Update a requirement and track changes"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], requirement.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.json
        current_user = get_current_user()
        
        # Defensive: group_id must not be empty
        if 'group_id' in data and not data['group_id']:
            return jsonify({'success': False, 'error': 'Group is required'}), 400
        
        # If group_id is being changed, verify the new group belongs to the same project
        if 'group_id' in data and data['group_id'] and requirement.group_id != data['group_id']:
            new_group = Group.query.get(data['group_id'])
            if not new_group or new_group.project_id != requirement.project_id:
                return jsonify({'success': False, 'error': 'Group not found or does not belong to this project'}), 400
        
        # Track changes for each field
        fields_to_track = ['title', 'description', 'status', 'chapter']
        for field in fields_to_track:
            if field in data and getattr(requirement, field) != data[field]:
                # Record the change
                history = CellHistory(
                    requirement_id=requirement.id,
                    field_name=field,
                    old_value=str(getattr(requirement, field)),
                    new_value=str(data[field]),
                    changed_by=current_user
                )
                db.session.add(history)
                # Update the field
                setattr(requirement, field, data[field])
        
        # Handle group_id separately
        if 'group_id' in data and data['group_id']:
            if requirement.group_id != data['group_id']:
                history = CellHistory(
                    requirement_id=requirement.id,
                    field_name='group_id',
                    old_value=str(requirement.group_id),
                    new_value=str(data['group_id']),
                    changed_by=current_user
                )
                db.session.add(history)
                requirement.group_id = data['group_id']
        
        requirement.updated_by = current_user
        requirement.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Requirement updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements', methods=['POST'])
@login_required
def create_requirement():
    """Create a new requirement"""
    try:
        data = request.json
        current_user = get_current_user()
        
        if not data.get('project_id'):
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        group_id = data.get('group_id')
        if not group_id:
            return jsonify({'success': False, 'error': 'Group is required'}), 400
        
        user = User.query.get(session['user_id'])
        project = Project.query.get(data['project_id'])
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if user has access to this project
        if user not in project.users:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Verify group belongs to this project
        group = Group.query.get(group_id)
        if not group or group.project_id != data['project_id']:
            return jsonify({'success': False, 'error': 'Group not found or does not belong to this project'}), 400
        
        requirement = Requirement(
            requirement_id=data['requirement_id'],
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'Draft'),
            chapter=data.get('chapter'),
            group_id=group_id,
            project_id=data['project_id'],
            created_by=current_user,
            updated_by=current_user
        )
        
        db.session.add(requirement)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Requirement created successfully',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['DELETE'])
@login_required
def delete_requirement(requirement_id):
    """Soft delete a requirement by setting status to 'deleted'"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], requirement.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Soft delete: set status to 'deleted' instead of actually deleting
        old_status = requirement.status
        requirement.status = 'deleted'
        requirement.updated_at = datetime.utcnow()
        requirement.updated_by = get_current_user()
        
        # Add history entry for the status change
        history = CellHistory(
            requirement_id=requirement.id,
            field_name='status',
            old_value=old_status,
            new_value='deleted',
            changed_by=get_current_user()
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Requirement deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-excel', methods=['POST'])
@login_required
def upload_excel():
    """Upload and process Excel file (M2M parent-child)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload Excel file.'}), 400
        
        # Get project_id and group_id from form
        project_id = request.form.get('project_id')
        group_id = request.form.get('group_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        if not group_id:
            return jsonify({'success': False, 'error': 'Group ID is required'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Verify group belongs to this project
        group = Group.query.get(group_id)
        if not group or group.project_id != project_id:
            return jsonify({'success': False, 'error': 'Group not found or does not belong to this project'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        current_user = get_current_user()
        try:
            if filename.endswith('.xlsx'):
                df = pd.read_excel(filepath, engine='openpyxl')
            else:
                df = pd.read_excel(filepath, engine='xlrd')
            required_columns = ['Requirement ID', 'Title']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            records_processed = 0
            records_skipped = 0
            req_obj_by_excel_id = {}
            # First pass: Create all requirements (ignore parent-child for now)
            for _, row in df.iterrows():
                req_id = str(row.get('Requirement ID', f'REQ_{uuid.uuid4().hex[:8]}'))
                
                # Check if requirement already exists in this project
                existing_requirement = Requirement.query.filter_by(
                    requirement_id=req_id, 
                    project_id=project_id
                ).first()
                
                if existing_requirement:
                    # Skip this requirement and use the existing one
                    req_obj_by_excel_id[row.get('Requirement ID')] = existing_requirement
                    records_skipped += 1
                    continue
                
                requirement = Requirement(
                    requirement_id=req_id,
                    title=str(row.get('Title', '')),
                    description=str(row.get('Description', '')),
                    status=str(row.get('Status', 'Draft')),
                    group_id=group.id,
                    project_id=project_id,
                    created_by=current_user,
                    updated_by=current_user
                )
                db.session.add(requirement)
                db.session.flush()
                history = CellHistory(
                    requirement_id=requirement.id,
                    field_name='created',
                    old_value=None,
                    new_value=requirement.requirement_id,
                    changed_by=current_user
                )
                db.session.add(history)
                req_obj_by_excel_id[row.get('Requirement ID')] = requirement
                records_processed += 1
            db.session.flush()
            # Second pass: Create M2M parent-child links
            for _, row in df.iterrows():
                parent_excel_id = row.get('Parent ID')
                child_excel_id = row.get('Requirement ID')
                if parent_excel_id and parent_excel_id in req_obj_by_excel_id and child_excel_id in req_obj_by_excel_id:
                    child = req_obj_by_excel_id[child_excel_id]
                    parent = req_obj_by_excel_id[parent_excel_id]
                    if parent not in child.parents:
                        child.parents.append(parent)
            db.session.commit()
            os.remove(filepath)
            return jsonify({
                'success': True,
                'message': f'Successfully processed {records_processed} requirements, skipped {records_skipped} duplicates',
                'data': {
                    'records_processed': records_processed,
                    'records_skipped': records_skipped
                }
            })
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    """Upload and process CSV file (M2M parent-child)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload CSV file.'}), 400
        
        # Get project_id and group_id from form
        project_id = request.form.get('project_id')
        group_id = request.form.get('group_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        if not group_id:
            return jsonify({'success': False, 'error': 'Group ID is required'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Verify group belongs to this project
        group = Group.query.get(group_id)
        if not group or group.project_id != project_id:
            return jsonify({'success': False, 'error': 'Group not found or does not belong to this project'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        current_user = get_current_user()
        try:
            # Read CSV file
            df = pd.read_csv(filepath, encoding='utf-8')
            required_columns = ['Requirement ID', 'Title']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            records_processed = 0
            records_skipped = 0
            req_obj_by_csv_id = {}
            # First pass: Create all requirements (ignore parent-child for now)
            for _, row in df.iterrows():
                req_id = str(row.get('Requirement ID', f'REQ_{uuid.uuid4().hex[:8]}'))
                
                # Check if requirement already exists in this project
                existing_requirement = Requirement.query.filter_by(
                    requirement_id=req_id, 
                    project_id=project_id
                ).first()
                
                if existing_requirement:
                    # Skip this requirement and use the existing one
                    req_obj_by_csv_id[row.get('Requirement ID')] = existing_requirement
                    records_skipped += 1
                    continue
                
                requirement = Requirement(
                    requirement_id=req_id,
                    title=str(row.get('Title', '')),
                    description=str(row.get('Description', '')),
                    status=str(row.get('Status', 'Draft')),
                    group_id=group.id,
                    project_id=project_id,
                    created_by=current_user,
                    updated_by=current_user
                )
                db.session.add(requirement)
                db.session.flush()
                history = CellHistory(
                    requirement_id=requirement.id,
                    field_name='created',
                    old_value=None,
                    new_value=requirement.requirement_id,
                    changed_by=current_user
                )
                db.session.add(history)
                req_obj_by_csv_id[row.get('Requirement ID')] = requirement
                records_processed += 1
            db.session.flush()
            # Second pass: Create M2M parent-child links
            for _, row in df.iterrows():
                parent_csv_id = row.get('Parent ID')
                child_csv_id = row.get('Requirement ID')
                if parent_csv_id and parent_csv_id in req_obj_by_csv_id and child_csv_id in req_obj_by_csv_id:
                    child = req_obj_by_csv_id[child_csv_id]
                    parent = req_obj_by_csv_id[parent_csv_id]
                    if parent not in child.parents:
                        child.parents.append(parent)
            db.session.commit()
            os.remove(filepath)
            return jsonify({
                'success': True,
                'message': f'Successfully processed {records_processed} requirements, skipped {records_skipped} duplicates',
                'data': {
                    'records_processed': records_processed,
                    'records_skipped': records_skipped
                }
            })
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-excel', methods=['GET'])
@login_required
def export_excel():
    """Export requirements to Excel for a specific project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        requirements = Requirement.query.filter_by(project_id=project_id).all()
        
        # Prepare data for export
        data = []
        for req in requirements:
            data.append({
                'Requirement ID': req.requirement_id,
                'Title': req.title,
                'Description': req.description,
                'Status': req.status,
                'Group': req.group_obj.name if req.group_obj else 'Default',
                'Project': req.project.name if req.project else 'Default',
                'Parent IDs': ', '.join([p.requirement_id for p in req.parents]),
                'Created At': req.created_at,
                'Updated At': req.updated_at,
                'Created By': req.created_by,
                'Updated By': req.updated_by
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        filename = f'{project.name}_requirements_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-csv', methods=['GET'])
@login_required
def export_csv():
    """Export requirements to CSV for a specific project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        requirements = Requirement.query.filter_by(project_id=project_id).all()
        
        # Prepare data for export
        data = []
        for req in requirements:
            data.append({
                'Requirement ID': req.requirement_id,
                'Title': req.title,
                'Description': req.description,
                'Status': req.status,
                'Group': req.group_obj.name if req.group_obj else 'Default',
                'Project': req.project.name if req.project else 'Default',
                'Parent IDs': ', '.join([p.requirement_id for p in req.parents]),
                'Created At': req.created_at,
                'Updated At': req.updated_at,
                'Created By': req.created_by,
                'Updated By': req.updated_by
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        filename = f'{project.name}_requirements_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/requirements/<requirement_id>/move', methods=['POST'])
@login_required
def move_requirement(requirement_id):
    """Move a requirement to a different group within the same project"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], requirement.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        data = request.json
        new_group_id = data.get('new_group_id')
        
        if not new_group_id:
            return jsonify({'success': False, 'error': 'New group ID is required'}), 400
        
        # Check if new group exists and belongs to the same project
        new_group = Group.query.get(new_group_id)
        if not new_group:
            return jsonify({'success': False, 'error': 'New group not found'}), 404
        
        if new_group.project_id != requirement.project_id:
            return jsonify({'success': False, 'error': 'Cannot move requirement to a group in a different project'}), 400
        
        # Update requirement
        requirement.group_id = new_group_id
        requirement.updated_at = datetime.utcnow()
        
        # Add to history
        history = CellHistory(
            requirement_id=requirement.id,
            field_name='group_id',
            old_value=str(requirement.group_id) if requirement.group_id else None,
            new_value=str(new_group_id),
            changed_by=get_current_user()
        )
        db.session.add(history)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Requirement moved successfully',
            'data': requirement.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/batch-update', methods=['POST'])
@login_required
def batch_update_requirements():
    """Batch update multiple requirements within a project"""
    try:
        data = request.json
        requirement_ids = data.get('requirement_ids', [])
        updates = data.get('updates', {})
        project_id = data.get('project_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        if not requirement_ids:
            return jsonify({'success': False, 'error': 'No requirement IDs provided'}), 400
        
        if not updates:
            return jsonify({'success': False, 'error': 'No updates provided'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Validate updates
        allowed_fields = {'status', 'chapter', 'group_id'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            return jsonify({'success': False, 'error': f'Invalid fields: {", ".join(invalid_fields)}'}), 400
        
        # Check if group_id is valid if provided
        if 'group_id' in updates and updates['group_id']:
            group = Group.query.get(updates['group_id'])
            if not group or group.project_id != project_id:
                return jsonify({'success': False, 'error': 'Invalid group ID or group does not belong to this project'}), 400
        
        # Update requirements
        updated_count = 0
        current_user = get_current_user()
        
        for req_id in requirement_ids:
            requirement = Requirement.query.filter_by(requirement_id=req_id, project_id=project_id).first()
            if requirement:
                # Track changes for history
                changes = []
                
                # Update fields
                if 'status' in updates and updates['status']:
                    if requirement.status != updates['status']:
                        changes.append(('status', requirement.status, updates['status']))
                        requirement.status = updates['status']
                
                if 'chapter' in updates:
                    if requirement.chapter != updates['chapter']:
                        changes.append(('chapter', requirement.chapter, updates['chapter']))
                        requirement.chapter = updates['chapter']
                
                if 'group_id' in updates and updates['group_id']:
                    if requirement.group_id != updates['group_id']:
                        changes.append(('group_id', str(requirement.group_id) if requirement.group_id else None, str(updates['group_id'])))
                        requirement.group_id = updates['group_id']
                
                requirement.updated_at = datetime.utcnow()
                requirement.updated_by = current_user
                
                # Add history entries for changes
                for field_name, old_value, new_value in changes:
                    history = CellHistory(
                        requirement_id=requirement.id,
                        field_name=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=current_user
                    )
                    db.session.add(history)
                
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {updated_count} requirements',
            'updated_count': updated_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/graph', methods=['GET'])
@login_required
def get_requirements_graph():
    """Get requirements data formatted for graph visualization (many-to-many) for a specific project"""
    try:
        project_id = request.args.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID is required'}), 400
        
        # Check if user has access to this project
        has_access, user, project = check_project_access(session['user_id'], project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Exclude deleted requirements from graph view
        requirements = Requirement.query.filter_by(project_id=project_id).filter(Requirement.status != 'deleted').all()
        nodes = []
        edges = []
        for req in requirements:
            node = {
                'id': req.id,
                'label': f"{req.requirement_id}\n{req.title[:50]}{'...' if len(req.title) > 50 else ''}",
                'title': req.title,
                'requirement_id': req.requirement_id,
                'status': req.status,
                'group_name': req.group_obj.name if req.group_obj else 'Unknown',
                'description': req.description,
                'created_at': req.created_at.isoformat() if req.created_at else None,
                'updated_at': req.updated_at.isoformat() if req.updated_at else None,
                'x': req.graph_x,
                'y': req.graph_y
            }
            # Set node color based on status
            if req.status == 'Completed':
                node['color'] = '#28a745'
            elif req.status == 'In Progress':
                node['color'] = '#007bff'
            elif req.status == 'Review':
                node['color'] = '#ffc107'
            else:
                node['color'] = '#6c757d'
            nodes.append(node)
            # Add edges for all parent links
            for parent in req.parents:
                edges.append({
                    'from': parent.id,
                    'to': req.id,
                    'arrows': 'to',
                    'color': '#666',
                    'width': 2
                })
        return jsonify({
            'success': True,
            'data': {
                'nodes': nodes,
                'edges': edges
            }
        })
    except Exception as e:
        print(f"[DEBUG] Exception in get_requirements_graph: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>/parent', methods=['POST'])
@login_required
def set_requirement_parent(requirement_id):
    """Set or remove a parent-child relationship (many-to-many)"""
    try:
        data = request.json
        parent_id = data.get('parent_id')
        remove_only = data.get('remove_only', False)
        print(f"[DEBUG] Received parent-child update: child requirement_id={requirement_id}, parent_id={parent_id}, remove_only={remove_only}")
        
        child = Requirement.query.filter_by(requirement_id=requirement_id).first()
        print(f"[DEBUG] Resolved child requirement: {child}")
        if not child:
            print("[DEBUG] Child requirement not found")
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], child.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        if parent_id:
            parent = Requirement.query.filter_by(requirement_id=parent_id).first()
            print(f"[DEBUG] Resolved parent requirement: {parent}")
            if not parent:
                print("[DEBUG] Parent requirement not found")
                return jsonify({'success': False, 'error': 'Parent requirement not found'}), 404
            
            # Check if parent belongs to the same project
            if parent.project_id != child.project_id:
                print("[DEBUG] Parent requirement belongs to different project")
                return jsonify({'success': False, 'error': 'Parent requirement must belong to the same project'}), 400
            if remove_only:
                # Remove only this parent-child link
                print(f"[DEBUG] Current parents of child before removal: {[p.requirement_id for p in child.parents]}")
                if parent in child.parents:
                    child.parents.remove(parent)
                    db.session.commit()
                    print(f"[DEBUG] Removed parent-child link: {parent_id} -> {requirement_id}")
                    return jsonify({'success': True, 'message': 'Parent relationship deleted'})
                else:
                    print(f"[DEBUG] Link does not exist: {parent_id} -> {requirement_id} (idempotent delete)")
                    # Always return success for idempotent delete
                    return jsonify({'success': True, 'message': 'Parent relationship already deleted'})
            # Prevent self-link
            if parent.id == child.id:
                print("[DEBUG] Attempted to set requirement as its own parent")
                return jsonify({'success': False, 'error': 'Cannot set requirement as its own parent'}), 400
            # Prevent duplicate link
            if parent not in child.parents:
                child.parents.append(parent)
                db.session.commit()
                print(f"[DEBUG] Added parent-child link: {parent_id} -> {requirement_id}")
                return jsonify({'success': True, 'message': 'Parent relationship added'})
            else:
                print(f"[DEBUG] Link already exists: {parent_id} -> {requirement_id}")
                return jsonify({'success': True, 'message': 'Link already exists'})
        else:
            # Remove all parent links for this child
            child.parents = []
            db.session.commit()
            print(f"[DEBUG] Removed all parent links for child: {requirement_id}")
            return jsonify({'success': True, 'message': 'All parent relationships removed'})
    except Exception as e:
        db.session.rollback()
        print(f"[DEBUG] Exception in set_requirement_parent: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>/position', methods=['POST'])
@login_required
def update_requirement_position(requirement_id):
    """Update requirement position in graph"""
    try:
        data = request.json
        x = data.get('x')
        y = data.get('y')
        
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Check if user has access to the project this requirement belongs to
        has_access, user, project = check_project_access(session['user_id'], requirement.project_id)
        if not has_access:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        requirement.graph_x = x
        requirement.graph_y = y
        requirement.updated_at = datetime.utcnow()
        requirement.updated_by = get_current_user()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Position updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000) 
