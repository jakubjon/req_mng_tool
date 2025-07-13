import pandas as pd
import requests
import os
from datetime import datetime
from models import db, Requirement, CellHistory, ExcelUpload
import uuid

class RequirementService:
    """Service class for requirement management operations"""
    
    @staticmethod
    def get_all_requirements(filters=None):
        """Get all requirements with optional filtering"""
        query = Requirement.query
        
        if filters:
            if filters.get('status'):
                query = query.filter(Requirement.status == filters['status'])
            if filters.get('category'):
                query = query.filter(Requirement.category == filters['category'])
            if filters.get('parent_id'):
                query = query.filter(Requirement.parent_id == filters['parent_id'])
            if filters.get('priority'):
                query = query.filter(Requirement.priority == filters['priority'])
        
        return query.all()
    
    @staticmethod
    def get_requirement_by_id(requirement_id):
        """Get requirement by its ID"""
        return Requirement.query.filter_by(requirement_id=requirement_id).first()
    
    @staticmethod
    def create_requirement(data, user_id):
        """Create a new requirement"""
        requirement = Requirement(
            requirement_id=data['requirement_id'],
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'Draft'),
            parent_id=data.get('parent_id'),
            created_by=user_id,
            updated_by=user_id
        )
        
        db.session.add(requirement)
        db.session.commit()
        
        return requirement
    
    @staticmethod
    def update_requirement(requirement_id, data, user_id):
        """Update a requirement and track changes"""
        requirement = RequirementService.get_requirement_by_id(requirement_id)
        if not requirement:
            raise ValueError('Requirement not found')
        
        # Track changes for each field
        fields_to_track = ['title', 'description', 'status', 'parent_id']
        
        for field in fields_to_track:
            if field in data and getattr(requirement, field) != data[field]:
                # Record the change
                history = CellHistory(
                    requirement_id=requirement.id,
                    field_name=field,
                    old_value=str(getattr(requirement, field)),
                    new_value=str(data[field]),
                    changed_by=user_id
                )
                db.session.add(history)
                
                # Update the field
                setattr(requirement, field, data[field])
        
        requirement.updated_by = user_id
        requirement.updated_at = datetime.utcnow()
        
        db.session.commit()
        return requirement
    
    @staticmethod
    def get_requirement_history(requirement_id):
        """Get change history for a requirement"""
        requirement = RequirementService.get_requirement_by_id(requirement_id)
        if not requirement:
            return []
        
        return CellHistory.query.filter_by(requirement_id=requirement.id).order_by(CellHistory.changed_at.desc()).all()
    
    @staticmethod
    def get_children_tree(requirement_id):
        """Get complete children tree for a requirement"""
        requirement = RequirementService.get_requirement_by_id(requirement_id)
        if not requirement:
            return None
        
        def build_children_tree(req):
            children = []
            for child in req.children:
                child_data = {
                    'id': child.id,
                    'requirement_id': child.requirement_id,
                    'title': child.title,
                    'description': child.description,
                    'priority': child.priority,
                    'status': child.status,
                    'category': child.category,
                    'children': build_children_tree(child)
                }
                children.append(child_data)
            return children
        
        return {
            'requirement_id': requirement.requirement_id,
            'title': requirement.title,
            'children': build_children_tree(requirement)
        }
    
    @staticmethod
    def get_parents_tree(requirement_id):
        """Get complete parents tree for a requirement"""
        requirement = RequirementService.get_requirement_by_id(requirement_id)
        if not requirement:
            return None
        
        def build_parents_tree(req):
            parents = []
            if req.parent:
                parent_data = {
                    'id': req.parent.id,
                    'requirement_id': req.parent.requirement_id,
                    'title': req.parent.title,
                    'description': req.parent.description,
                    'priority': req.parent.priority,
                    'status': req.parent.status,
                    'category': req.parent.category,
                    'parents': build_parents_tree(req.parent)
                }
                parents.append(parent_data)
            return parents
        
        return {
            'requirement_id': requirement.requirement_id,
            'title': requirement.title,
            'parents': build_parents_tree(requirement)
        }

class ExcelService:
    """Service class for Excel file processing"""
    
    @staticmethod
    def process_excel_file(filepath, user_id):
        """Process Excel file and create requirements"""
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            
            # Validate required columns
            required_columns = ['Requirement ID', 'Title']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Record upload
            upload_record = ExcelUpload(
                filename=os.path.basename(filepath),
                uploaded_by=user_id,
                status='Processing'
            )
            db.session.add(upload_record)
            db.session.commit()
            
            processed_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Generate requirement ID if not provided
                    req_id = str(row.get('Requirement ID', f'REQ_{uuid.uuid4().hex[:8]}'))
                    
                    # Check if requirement already exists
                    existing = Requirement.query.filter_by(requirement_id=req_id).first()
                    if existing:
                        errors.append(f"Row {index + 2}: Requirement ID '{req_id}' already exists")
                        continue
                    
                    # Create requirement
                    requirement = Requirement(
                        requirement_id=req_id,
                        title=str(row.get('Title', '')),
                        description=str(row.get('Description', '')),
                        status=str(row.get('Status', 'Draft')),
                        priority=str(row.get('Priority', 'Medium')),
                        category=str(row.get('Category', '')),
                        parent_id=row.get('Parent ID') if pd.notna(row.get('Parent ID')) else None,
                        created_by=user_id,
                        updated_by=user_id
                    )
                    
                    db.session.add(requirement)
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
                    continue
            
            # Update upload record
            upload_record.status = 'Completed' if not errors else 'Completed with errors'
            upload_record.records_processed = processed_count
            if errors:
                upload_record.error_message = '\n'.join(errors[:10])  # Limit error messages
            
            db.session.commit()
            
            return {
                'success': True,
                'processed_count': processed_count,
                'errors': errors,
                'upload_id': upload_record.id
            }
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def export_requirements_to_excel():
        """Export all requirements to Excel format"""
        requirements = Requirement.query.all()
        
        data = []
        for req in requirements:
            data.append({
                'Requirement ID': req.requirement_id,
                'Title': req.title,
                'Description': req.description,
                'Priority': req.priority,
                'Status': req.status,
                'Category': req.category,
                'Parent ID': req.parent_id,
                'Created At': req.created_at,
                'Updated At': req.updated_at,
                'Created By': req.created_by,
                'Updated By': req.updated_by
            })
        
        df = pd.DataFrame(data)
        return df

class DirectusService:
    """Service class for Directus integration"""
    
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_current_user(self):
        """Get current user from Directus"""
        try:
            response = requests.get(f"{self.base_url}/users/me", headers=self.headers)
            if response.status_code == 200:
                return response.json()['data']
            return None
        except Exception:
            return None
    
    def create_user(self, user_data):
        """Create a new user in Directus"""
        try:
            response = requests.post(f"{self.base_url}/users", headers=self.headers, json=user_data)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None
    
    def get_users(self):
        """Get all users from Directus"""
        try:
            response = requests.get(f"{self.base_url}/users", headers=self.headers)
            if response.status_code == 200:
                return response.json()['data']
            return []
        except Exception:
            return []
    
    def sync_requirements_to_directus(self, requirements):
        """Sync requirements to Directus (if needed)"""
        # This would be implemented based on your Directus schema
        pass 