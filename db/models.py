from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

from . import db

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary (without password)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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

# Association table for many-to-many parent-child links
requirement_links = db.Table(
    'requirement_links',
    db.Column('parent_id', db.String(36), db.ForeignKey('requirements.id'), primary_key=True),
    db.Column('child_id', db.String(36), db.ForeignKey('requirements.id'), primary_key=True)
)

class Requirement(db.Model):
    """Requirement model with parent-child relationships within groups"""
    __tablename__ = 'requirements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='Draft')
    group_id = db.Column(db.String(36), db.ForeignKey('groups.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    chapter = db.Column(db.String(100))
    graph_x = db.Column(db.Float, nullable=True)  # X position in graph
    graph_y = db.Column(db.Float, nullable=True)  # Y position in graph
    
    # Many-to-many parent-child relationships
    parents = relationship(
        'Requirement',
        secondary=requirement_links,
        primaryjoin=id==requirement_links.c.child_id,
        secondaryjoin=id==requirement_links.c.parent_id,
        backref='children_m2m'
    )
    
    # REMOVED: Self-referential relationship for parent-child (within same group)
    # children = db.relationship(
    #     'Requirement',
    #     backref=db.backref('parent', remote_side=[id]),
    #     cascade='all, delete-orphan',
    #     lazy='dynamic'
    # )
    
    def __repr__(self):
        return f'<Requirement {self.requirement_id}: {self.title}>'
    
    def to_dict(self, shallow=False):
        """Convert requirement to dictionary. If shallow, only include IDs for children/parents."""
        data = {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'chapter': self.chapter,
            'group_id': self.group_id,
            'group_name': self.group_obj.name if self.group_obj else None,
            'parents': [p.requirement_id for p in self.parents],
            'parent_objs': [
                {'requirement_id': p.requirement_id, 'title': p.title}
                for p in self.parents
            ],
            'children_count': len(self.children_m2m),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'graph_x': self.graph_x,
            'graph_y': self.graph_y
        }
        if shallow:
            # Only include children as IDs
            data['children'] = [c.requirement_id for c in self.children_m2m]
        else:
            # Full child objects (but shallow=True for their children to prevent deep recursion)
            data['children'] = [c.to_dict(shallow=True) for c in self.children_m2m]
        return data

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
