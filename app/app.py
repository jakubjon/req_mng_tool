from flask import Flask, request, jsonify, send_file, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
import uuid
from dotenv import load_dotenv
from app.db import db
from app.models import Requirement, CellHistory, Group, User
from app.config import config

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config.from_object(config['development'])
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import db from models and initialize it
db.init_app(app)

# Directus configuration
DIRECTUS_URL = os.getenv('DIRECTUS_URL', 'http://localhost:8055')
DIRECTUS_TOKEN = os.getenv('DIRECTUS_TOKEN')

# Directus API helper functions
def get_directus_headers():
    return {
        'Authorization': f'Bearer {DIRECTUS_TOKEN}',
        'Content-Type': 'application/json'
    }

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

# Web Routes
@app.route('/')
def index():
    """Serve the main application interface"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    if 'user_id' in session:
        return redirect(url_for('index'))
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
        email = data.get('email')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
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
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    })

# API Routes
@app.route('/api/groups', methods=['GET'])
def get_groups():
    """Get all groups with hierarchy"""
    try:
        # Get all groups
        groups = Group.query.all()
        
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
def create_group():
    """Create a new group"""
    try:
        data = request.json
        current_user = get_current_user()
        
        group = Group(
            name=data['name'],
            description=data.get('description', ''),
            parent_id=data.get('parent_id')
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
def update_group(group_id):
    """Update a group"""
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Group not found'}), 404
        
        data = request.json
        
        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'parent_id' in data:
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
def delete_group(group_id):
    """Delete a group"""
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Group not found'}), 404
        
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
def get_requirements():
    """Get all requirements with optional filtering"""
    try:
        # Query parameters for filtering
        status = request.args.get('status')
        chapter = request.args.get('chapter')
        group_id = request.args.get('group_id')
        parent_id = request.args.get('parent_id')
        
        query = Requirement.query
        
        if status:
            query = query.filter(Requirement.status == status)
        if chapter:
            query = query.filter(Requirement.chapter == chapter)
        if group_id:
            query = query.filter(Requirement.group_id == group_id)
        if parent_id:
            query = query.filter(Requirement.parent_id == parent_id)
        
        requirements = query.all()
        
        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in requirements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['GET'])
def get_requirement(requirement_id):
    """Get a specific requirement with details"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Get history
        history = CellHistory.query.filter_by(requirement_id=requirement.id).order_by(CellHistory.changed_at.desc()).all()
        
        # Get children
        children = requirement.children.all()
        
        data = requirement.to_dict()
        data['history'] = [h.to_dict() for h in history]
        data['children'] = [c.to_dict() for c in children]
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>', methods=['PUT'])
def update_requirement(requirement_id):
    """Update a requirement and track changes"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        data = request.json
        current_user = get_current_user()
        # Defensive: group_id must not be empty
        if 'group_id' in data and not data['group_id']:
            return jsonify({'success': False, 'error': 'Group is required'}), 400
        # Track changes for each field
        fields_to_track = ['title', 'description', 'status', 'chapter', 'parent_id']
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
def create_requirement():
    """Create a new requirement"""
    try:
        data = request.json
        current_user = get_current_user()
        group_id = data.get('group_id')
        if not group_id:
            return jsonify({'success': False, 'error': 'Group is required'}), 400
        requirement = Requirement(
            requirement_id=data['requirement_id'],
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'Draft'),
            chapter=data.get('chapter'),
            group_id=group_id,
            parent_id=data.get('parent_id'),
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
def delete_requirement(requirement_id):
    """Delete a requirement"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        db.session.delete(requirement)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Requirement deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    """Upload and process Excel file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload Excel file.'}), 400
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Get group_id from form
        group_id = request.form.get('group_id')
        if not group_id:
            raise ValueError('No group selected for import.')
        group = Group.query.get(group_id)
        if not group:
            raise ValueError('Selected group does not exist.')
        current_user = get_current_user()
        # Process Excel file
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
            requirement_id_mapping = {}
            # First pass: Create parent requirements
            for _, row in df.iterrows():
                if pd.isna(row.get('Parent ID')) or row.get('Parent ID') == '':
                    requirement = Requirement(
                        requirement_id=str(row.get('Requirement ID', f'REQ_{uuid.uuid4().hex[:8]}')),
                        title=str(row.get('Title', '')),
                        description=str(row.get('Description', '')),
                        status=str(row.get('Status', 'Draft')),
                        group_id=group.id,
                        parent_id=None,
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
                    requirement_id_mapping[row.get('Requirement ID')] = requirement.id
                    records_processed += 1
            # Second pass: Create child requirements
            for _, row in df.iterrows():
                parent_requirement_id = row.get('Parent ID')
                if not pd.isna(parent_requirement_id) and parent_requirement_id != '':
                    if parent_requirement_id in requirement_id_mapping:
                        requirement = Requirement(
                            requirement_id=str(row.get('Requirement ID', f'REQ_{uuid.uuid4().hex[:8]}')),
                            title=str(row.get('Title', '')),
                            description=str(row.get('Description', '')),
                            status=str(row.get('Status', 'Draft')),
                            group_id=group.id,
                            parent_id=requirement_id_mapping[parent_requirement_id],
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
                        records_processed += 1
            os.remove(filepath)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Successfully processed {records_processed} requirements',
                'data': {
                    'records_processed': records_processed
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
def export_excel():
    """Export requirements to Excel"""
    try:
        requirements = Requirement.query.all()
        
        # Prepare data for export
        data = []
        for req in requirements:
            data.append({
                'Requirement ID': req.requirement_id,
                'Title': req.title,
                'Description': req.description,
                'Status': req.status,
                'Group': req.group_obj.name if req.group_obj else 'Default',
                'Parent ID': req.parent.requirement_id if req.parent else '',
                'Created At': req.created_at,
                'Updated At': req.updated_at,
                'Created By': req.created_by,
                'Updated By': req.updated_by
            })
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        filename = f'requirements_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        df.to_excel(filepath, index=False, engine='openpyxl')
        
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
def move_requirement(requirement_id):
    """Move a requirement to a different group"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        data = request.json
        new_group_id = data.get('new_group_id')
        
        if not new_group_id:
            return jsonify({'success': False, 'error': 'New group ID is required'}), 400
        
        # Check if new group exists
        new_group = Group.query.get(new_group_id)
        if not new_group:
            return jsonify({'success': False, 'error': 'New group not found'}), 404
        
        # Update requirement
        requirement.group_id = new_group_id
        requirement.parent_id = None  # Remove parent relationship when moving
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
def batch_update_requirements():
    """Batch update multiple requirements"""
    try:
        data = request.json
        requirement_ids = data.get('requirement_ids', [])
        updates = data.get('updates', {})
        
        if not requirement_ids:
            return jsonify({'success': False, 'error': 'No requirement IDs provided'}), 400
        
        if not updates:
            return jsonify({'success': False, 'error': 'No updates provided'}), 400
        
        # Validate updates
        allowed_fields = {'status', 'chapter', 'group_id'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            return jsonify({'success': False, 'error': f'Invalid fields: {", ".join(invalid_fields)}'}), 400
        
        # Check if group_id is valid if provided
        if 'group_id' in updates and updates['group_id']:
            group = Group.query.get(updates['group_id'])
            if not group:
                return jsonify({'success': False, 'error': 'Invalid group ID'}), 400
        
        # Update requirements
        updated_count = 0
        current_user = get_current_user()
        
        for req_id in requirement_ids:
            requirement = Requirement.query.filter_by(requirement_id=req_id).first()
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
def get_requirements_graph():
    """Get requirements data formatted for graph visualization"""
    try:
        # Get all requirements with their relationships
        requirements = Requirement.query.all()
        
        # Format data for Vis.js network
        nodes = []
        edges = []
        
        for req in requirements:
            # Create node
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
                node['color'] = '#28a745'  # Green
            elif req.status == 'In Progress':
                node['color'] = '#007bff'  # Blue
            elif req.status == 'Review':
                node['color'] = '#ffc107'  # Yellow
            else:  # Draft
                node['color'] = '#6c757d'  # Gray
                
            nodes.append(node)
            
            # Create edge if there's a parent relationship
            if req.parent_id:
                edges.append({
                    'from': req.parent_id,
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
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>/parent', methods=['POST'])
def set_requirement_parent(requirement_id):
    """Set parent-child relationship between requirements"""
    try:
        data = request.json
        parent_id = data.get('parent_id')
        
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        # Validate parent exists if provided
        if parent_id:
            parent = Requirement.query.filter_by(requirement_id=parent_id).first()
            if not parent:
                return jsonify({'success': False, 'error': 'Parent requirement not found'}), 404
            
            # Prevent circular references
            if parent_id == requirement.requirement_id:
                return jsonify({'success': False, 'error': 'Cannot set requirement as its own parent'}), 400
            
            # Check if this would create a circular reference
            def has_circular_reference(child_id, target_parent_id):
                if child_id == target_parent_id:
                    return True
                child = Requirement.query.filter_by(requirement_id=child_id).first()
                if child and child.parent_id:
                    return has_circular_reference(child.parent_id, target_parent_id)
                return False
            
            if has_circular_reference(parent_id, requirement.requirement_id):
                return jsonify({'success': False, 'error': 'This would create a circular reference'}), 400
            
            requirement.parent_id = parent.id
        else:
            requirement.parent_id = None
        
        requirement.updated_at = datetime.utcnow()
        requirement.updated_by = get_current_user()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Parent relationship updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/requirements/<requirement_id>/position', methods=['POST'])
def update_requirement_position(requirement_id):
    """Update requirement position in graph"""
    try:
        data = request.json
        x = data.get('x')
        y = data.get('y')
        
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
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