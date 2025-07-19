#!/usr/bin/env python3
"""
Script to create a sample Excel file with example requirements
"""
import pandas as pd
import uuid
import os
import sys
from datetime import datetime

# Allow importing models without loading the entire application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Requirement, Group

def create_sample_requirements():
    """Create sample requirements data"""
    
    # Sample requirements with parent-child relationships
    requirements_data = [
        # Group: Authentication & Security
        {
            'Requirement ID': 'REQ-001',
            'Title': 'User Authentication System',
            'Description': 'Implement secure user authentication and authorization system',
            'Status': 'In Progress',
            'Parent ID': None
        },
        {
            'Requirement ID': 'REQ-001-01',
            'Title': 'Login Functionality',
            'Description': 'Implement user login with email/password authentication',
            'Status': 'In Progress',
            'Parent ID': 'REQ-001'
        },
        {
            'Requirement ID': 'REQ-001-02',
            'Title': 'Password Reset',
            'Description': 'Implement secure password reset functionality with email verification',
            'Status': 'Not Started',
            'Parent ID': 'REQ-001'
        },
        {
            'Requirement ID': 'REQ-001-03',
            'Title': 'Role-Based Access Control',
            'Description': 'Implement role-based permissions and access control',
            'Status': 'Planning',
            'Parent ID': 'REQ-001'
        },
        
        # Group: Backend Infrastructure
        {
            'Requirement ID': 'REQ-002',
            'Title': 'Database Management',
            'Description': 'Design and implement database schema and management system',
            'Status': 'Completed',
            'Parent ID': None
        },
        {
            'Requirement ID': 'REQ-002-01',
            'Title': 'Database Schema Design',
            'Description': 'Design normalized database schema for requirements management',
            'Status': 'Completed',
            'Parent ID': 'REQ-002'
        },
        {
            'Requirement ID': 'REQ-002-02',
            'Title': 'Data Migration Scripts',
            'Description': 'Create scripts for data migration and backup procedures',
            'Status': 'In Progress',
            'Parent ID': 'REQ-002'
        },
        {
            'Requirement ID': 'REQ-002-03',
            'Title': 'Database Performance Optimization',
            'Description': 'Optimize database queries and add appropriate indexes',
            'Status': 'Not Started',
            'Parent ID': 'REQ-002'
        },
        
        # Group: User Interface
        {
            'Requirement ID': 'REQ-003',
            'Title': 'User Interface Design',
            'Description': 'Create responsive and user-friendly web interface',
            'Status': 'Planning',
            'Parent ID': None
        },
        {
            'Requirement ID': 'REQ-003-01',
            'Title': 'Responsive Design',
            'Description': 'Ensure interface works on desktop, tablet, and mobile devices',
            'Status': 'Planning',
            'Parent ID': 'REQ-003'
        },
        {
            'Requirement ID': 'REQ-003-02',
            'Title': 'Accessibility Compliance',
            'Description': 'Implement WCAG 2.1 AA accessibility standards',
            'Status': 'Not Started',
            'Parent ID': 'REQ-003'
        },
        
        # Group: Quality Assurance
        {
            'Requirement ID': 'REQ-005',
            'Title': 'Testing Framework',
            'Description': 'Implement automated testing framework with unit and integration tests',
            'Status': 'In Progress',
            'Parent ID': None
        },
        {
            'Requirement ID': 'REQ-005-01',
            'Title': 'Unit Tests',
            'Description': 'Write unit tests for all business logic functions',
            'Status': 'In Progress',
            'Parent ID': 'REQ-005'
        },
        {
            'Requirement ID': 'REQ-005-02',
            'Title': 'Integration Tests',
            'Description': 'Create integration tests for API endpoints',
            'Status': 'Not Started',
            'Parent ID': 'REQ-005'
        },
        {
            'Requirement ID': 'REQ-005-03',
            'Title': 'End-to-End Tests',
            'Description': 'Implement end-to-end tests for critical user workflows',
            'Status': 'Not Started',
            'Parent ID': 'REQ-005'
        },
        
        # Group: Documentation & DevOps
        {
            'Requirement ID': 'REQ-004',
            'Title': 'API Documentation',
            'Description': 'Create comprehensive API documentation using OpenAPI/Swagger',
            'Status': 'Not Started',
            'Parent ID': None
        },
        {
            'Requirement ID': 'REQ-006',
            'Title': 'Deployment Pipeline',
            'Description': 'Set up CI/CD pipeline for automated deployment',
            'Status': 'Planning',
            'Parent ID': None
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(requirements_data)
    
    # Save to Excel file
    filename = 'sample_requirements.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Requirements', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Requirements']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"✅ Sample requirements file created: {filename}")
    print(f"📊 Total requirements: {len(requirements_data)}")
    print(f"📈 Statuses: {', '.join(df['Status'].unique())}")
    
    # Show requirements
    print("\n📋 Requirements:")
    for _, row in df.iterrows():
        indent = "  " * (row['Parent ID'].count('-') if row['Parent ID'] else 0)
        print(f"{indent}• {row['Requirement ID']}: {row['Title']} - {row['Description']}")

if __name__ == "__main__":
    create_sample_requirements() 
