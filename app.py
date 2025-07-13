from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import pandas as pd
import requests
import json
from datetime import datetime
import uuid
from dotenv import load_dotenv
import io
import base64
from models import db, Requirement, CellHistory, Group, ExcelUpload
from config import config

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config.from_object(config['development'])
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Directus configuration
DIRECTUS_URL = os.getenv('DIRECTUS_URL', 'http://localhost:8055')
DIRECTUS_TOKEN = os.getenv('DIRECTUS_TOKEN')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import db from models and initialize it
db.init_app(app)

# Directus API helper functions
def get_directus_headers():
    return {
        'Authorization': f'Bearer {DIRECTUS_TOKEN}',
        'Content-Type': 'application/json'
    }

def get_current_user():
    """Get current user from Directus (simplified - in real app, use proper auth)"""
    # This is a simplified version - in a real app, you'd get this from the session/token
    return request.headers.get('X-User-ID', 'unknown_user')

# Web Routes
@app.route('/')
def index():
    """Serve the main application interface"""
    return render_template('index.html')

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

@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    """Get all requirements with optional filtering"""
    try:
        # Query parameters for filtering
        status = request.args.get('status')
        category = request.args.get('category')
        group_id = request.args.get('group_id')
        parent_id = request.args.get('parent_id')
        priority = request.args.get('priority')
        
        query = Requirement.query
        
        if status:
            query = query.filter(Requirement.status == status)
        if category:
            query = query.filter(Requirement.category == category)
        if group_id:
            query = query.filter(Requirement.group_id == group_id)
        if parent_id:
            query = query.filter(Requirement.parent_id == parent_id)
        if priority:
            query = query.filter(Requirement.priority == priority)
        
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
        fields_to_track = ['title', 'description', 'status', 'priority', 'category', 'parent_id']
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
            priority=data.get('priority', 'Medium'),
            category=data.get('category', ''),
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
                        priority=str(row.get('Priority', 'Medium')),
                        category=str(row.get('Category', '')),
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
                            priority=str(row.get('Priority', 'Medium')),
                            category=str(row.get('Category', '')),
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
                'Priority': req.priority,
                'Status': req.status,
                'Category': req.category,
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
    """Move a requirement to a different group (parent-child links persist)"""
    try:
        requirement = Requirement.query.filter_by(requirement_id=requirement_id).first()
        if not requirement:
            return jsonify({'success': False, 'error': 'Requirement not found'}), 404
        
        data = request.json
        new_group_id = data.get('group_id')
        if not new_group_id:
            return jsonify({'success': False, 'error': 'Group ID is required'}), 400
        
        current_user = get_current_user()
        old_group_id = requirement.group_id
        
        # Record the change
        history = CellHistory(
            requirement_id=requirement.id,
            field_name='group_id',
            old_value=old_group_id,
            new_value=new_group_id,
            changed_by=current_user
        )
        db.session.add(history)
        
        # Update the requirement's group only
        requirement.group_id = new_group_id
        requirement.updated_by = current_user
        requirement.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Requirement moved to new group'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000) 