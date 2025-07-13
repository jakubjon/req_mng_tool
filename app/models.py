from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Create db instance here to avoid circular imports
db = SQLAlchemy()

class Group(db.Model):
    """Group model with parent-child relationships"""
    __tablename__ = 'groups'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.String(36), db.ForeignKey('groups.id'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for parent-child
    children = db.relationship(
        'Group',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    # Relationship to requirements
    requirements = db.relationship('Requirement', backref='group_obj', lazy='dynamic')
    
    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'children_count': self.children.count(),
            'requirements_count': self.requirements.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Requirement(db.Model):
    """Requirement model with parent-child relationships within groups"""
    __tablename__ = 'requirements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Draft')
    category = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='Medium')  # Added missing priority field
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id'), nullable=False, index=True)
    parent_id = db.Column(db.String(36), db.ForeignKey('requirements.id'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Self-referential relationship for parent-child (within same group)
    children = db.relationship(
        'Requirement',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    def __repr__(self):
        return f'<Requirement {self.requirement_id}: {self.title}>'
    
    def to_dict(self):
        """Convert requirement to dictionary"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'category': self.category,
            'priority': self.priority,  # Added priority to dict
            'group_id': self.group_id,
            'group_name': self.group_obj.name if self.group_obj else None,
            'parent_id': self.parent_id,
            'children_count': self.children.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by
        }

class CellHistory(db.Model):
    """Model to track changes to requirement fields"""
    __tablename__ = 'cell_history'
    
    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.String(36), db.ForeignKey('requirements.id'), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.String(100), nullable=False)
    
    # Relationship to requirement
    requirement = db.relationship('Requirement', backref='history')
    
    def __repr__(self):
        return f'<CellHistory {self.field_name}: {self.old_value} -> {self.new_value}>'
    
    def to_dict(self):
        """Convert history record to dictionary"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'changed_by': self.changed_by
        }

class ExcelUpload(db.Model):
    """Model to track Excel file uploads"""
    __tablename__ = 'excel_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Processing')  # Processing, Completed, Failed
    records_processed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ExcelUpload {self.filename}: {self.status}>'
    
    def to_dict(self):
        """Convert upload record to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'status': self.status,
            'records_processed': self.records_processed,
            'error_message': self.error_message
        } 