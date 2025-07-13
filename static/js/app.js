// Global variables
let currentRequirementId = null;
let currentGroupId = null;
let requirementsData = [];
let groupsData = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    setupEventListeners();
    // Populate upload group dropdown
    loadUploadGroupOptions();
});

// Setup event listeners
function setupEventListeners() {
    // File upload
    const fileInput = document.getElementById('excel-file');
    const uploadArea = document.getElementById('upload-area');
    
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#dee2e6';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#dee2e6';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload();
        }
    });
    
    // Search and filters
    document.getElementById('search-input').addEventListener('input', filterRequirements);
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionName + '-section').style.display = 'block';
    
    // Add active class to clicked nav link
    event.target.classList.add('active');
    
    // Load section-specific data
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'requirements':
            loadGroups();
            loadRequirements();
            break;
        case 'upload':
            break;
    }
}

// Dashboard functions
async function loadDashboard() {
    try {
        const response = await fetch('/api/requirements');
        const data = await response.json();
        
        if (data.success) {
            const requirements = data.data;
            requirementsData = requirements;
            
            // Update dashboard stats
            document.getElementById('total-requirements').textContent = requirements.length;
            document.getElementById('draft-requirements').textContent = 
                requirements.filter(r => r.status === 'Draft').length;
            document.getElementById('completed-requirements').textContent = 
                requirements.filter(r => r.status === 'Completed').length;
            document.getElementById('high-priority').textContent = 
                requirements.filter(r => r.priority === 'High').length;
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showAlert('Error loading dashboard data', 'danger');
    }
}

// Group functions
async function loadGroups() {
    try {
        const response = await fetch('/api/groups');
        const data = await response.json();
        
        if (data.success) {
            groupsData = data.data;
            renderGroupTree(groupsData);
            loadGroupOptions();
        }
    } catch (error) {
        console.error('Error loading groups:', error);
        showAlert('Error loading groups', 'danger');
    }
}

function renderGroupTree(groups) {
    const treeContainer = document.getElementById('group-tree');
    
    function buildGroupHtml(groupList, level = 0) {
        return groupList.map(group => `
            <div class="group-node" data-group-id="${group.id}" onclick="selectGroup('${group.id}')">
                <div class="d-flex align-items-center">
                    ${group.children && group.children.length > 0 ? 
                        `<i class="fas fa-chevron-right group-expand-btn" onclick="toggleGroupExpansion(event, '${group.id}')"></i>` : 
                        '<i class="fas fa-folder me-2"></i>'
                    }
                    <div class="flex-grow-1">
                        <div class="group-name">${group.name}</div>
                        <div class="group-count">${group.requirements_count} requirements</div>
                    </div>
                </div>
                ${group.children && group.children.length > 0 ? 
                    `<div class="group-children" id="group-children-${group.id}" style="display: none;">
                        ${buildGroupHtml(group.children, level + 1)}
                    </div>` : ''
                }
            </div>
        `).join('');
    }
    
    treeContainer.innerHTML = buildGroupHtml(groups);
}

function toggleGroupExpansion(event, groupId) {
    event.stopPropagation();
    const btn = event.target;
    const children = document.getElementById(`group-children-${groupId}`);
    
    if (children.style.display === 'none') {
        children.style.display = 'block';
        btn.classList.add('expanded');
    } else {
        children.style.display = 'none';
        btn.classList.remove('expanded');
    }
}

function selectGroup(groupId) {
    // Remove previous selection
    document.querySelectorAll('.group-node').forEach(node => {
        node.classList.remove('selected');
    });
    
    // Add selection to clicked group
    const selectedNode = document.querySelector(`[data-group-id="${groupId}"]`);
    if (selectedNode) {
        selectedNode.classList.add('selected');
    }
    
    currentGroupId = groupId;
    loadRequirements(groupId);
}

function loadGroupOptions() {
    const groupSelect = document.getElementById('req-group-id');
    const groupParentSelect = document.getElementById('group-parent-id');
    
    function populateSelect(select, groups, level = 0) {
        select.innerHTML = '<option value="">Select a group</option>';
        
        groups.forEach(group => {
            const indent = '&nbsp;'.repeat(level * 4);
            const option = document.createElement('option');
            option.value = group.id;
            option.innerHTML = indent + group.name;
            select.appendChild(option);
            
            if (group.children && group.children.length > 0) {
                populateSelect(select, group.children, level + 1);
            }
        });
    }
    
    populateSelect(groupSelect, groupsData);
    populateSelect(groupParentSelect, groupsData);
}

// Group modal functions
function showAddGroupModal() {
    document.getElementById('group-modal-title').textContent = 'Add Group';
    document.getElementById('group-form').reset();
    loadGroupOptions();
    
    const modal = new bootstrap.Modal(document.getElementById('groupModal'));
    modal.show();
}

async function saveGroup() {
    const formData = {
        name: document.getElementById('group-name').value,
        description: document.getElementById('group-description').value,
        parent_id: document.getElementById('group-parent-id').value || null
    };
    
    try {
        const response = await fetch('/api/groups', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': 'current_user'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Group created successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('groupModal')).hide();
            loadGroups();
        } else {
            showAlert(data.error || 'Error creating group', 'danger');
        }
    } catch (error) {
        console.error('Error creating group:', error);
        showAlert('Error creating group', 'danger');
    }
}

// Requirements functions
async function loadRequirements(groupId = null) {
    try {
        let url = '/api/requirements';
        if (groupId) {
            url += `?group_id=${groupId}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            requirementsData = data.data;
            renderRequirementsTable(requirementsData);
        }
    } catch (error) {
        console.error('Error loading requirements:', error);
        showAlert('Error loading requirements', 'danger');
    }
}

function renderRequirementsTable(requirements) {
    const tbody = document.getElementById('requirements-table-body');
    tbody.innerHTML = '';
    requirements.forEach(req => {
        const row = document.createElement('tr');
        row.className = 'requirement-row';
        row.onclick = () => showRequirementDetails(req.requirement_id);
        row.innerHTML = `
            <td>${req.requirement_id}</td>
            <td>${req.title}</td>
            <td>${req.description ? req.description : ''}</td>
            <td>${req.status}</td>
            <td>${req.children_count}</td>
            <td>${formatDate(req.updated_at)}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="event.stopPropagation(); editRequirement('${req.requirement_id}')"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteRequirement('${req.requirement_id}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function filterRequirements() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const filtered = requirementsData.filter(req => {
        return (
            req.title.toLowerCase().includes(searchTerm) ||
            req.requirement_id.toLowerCase().includes(searchTerm) ||
            (req.description && req.description.toLowerCase().includes(searchTerm))
        );
    });
    renderRequirementsTable(filtered);
}

// Modal functions
function showAddRequirementModal() {
    document.getElementById('modal-title').textContent = 'Add Requirement';
    document.getElementById('requirement-form').reset();
    currentRequirementId = null;
    // Load parent options
    loadParentOptions();
    loadGroupOptions();
    // Set group dropdown to currentGroupId
    if (currentGroupId) {
        document.getElementById('req-group-id').value = currentGroupId;
    }
    const modal = new bootstrap.Modal(document.getElementById('requirementModal'));
    modal.show();
}

function editRequirement(requirementId) {
    const requirement = requirementsData.find(r => r.requirement_id === requirementId);
    if (!requirement) return;
    document.getElementById('modal-title').textContent = 'Edit Requirement';
    currentRequirementId = requirementId;
    // Populate form
    document.getElementById('req-id').value = requirement.requirement_id;
    document.getElementById('req-title').value = requirement.title;
    document.getElementById('req-description').value = requirement.description || '';
    document.getElementById('req-status').value = requirement.status;
    loadParentOptions(requirement.parent_id);
    loadGroupOptions();
    // Set group dropdown to requirement's group
    if (requirement.group_id) {
        document.getElementById('req-group-id').value = requirement.group_id;
    }
    const modal = new bootstrap.Modal(document.getElementById('requirementModal'));
    modal.show();
}

async function loadParentOptions(selectedParentId = '') {
    try {
        const response = await fetch('/api/requirements');
        const data = await response.json();
        
        if (data.success) {
            const parentSelect = document.getElementById('parent-id');
            parentSelect.innerHTML = '<option value="">No Parent</option>';
            
            data.data.forEach(req => {
                const option = document.createElement('option');
                option.value = req.requirement_id;
                option.textContent = `${req.requirement_id} - ${req.title}`;
                if (req.requirement_id === selectedParentId) {
                    option.selected = true;
                }
                parentSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading parent options:', error);
    }
}

async function saveRequirement() {
    const formData = {
        requirement_id: document.getElementById('req-id').value,
        title: document.getElementById('req-title').value,
        description: document.getElementById('req-description').value,
        status: document.getElementById('req-status').value,
        parent_id: document.getElementById('parent-id').value || null
    };
    const groupId = document.getElementById('req-group-id').value;
    if (groupId) {
        formData.group_id = groupId;
    }
    
    try {
        const url = currentRequirementId ? 
            `/api/requirements/${currentRequirementId}` : 
            '/api/requirements';
        
        const method = currentRequirementId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': 'current_user'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Requirement saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('requirementModal')).hide();
            loadRequirements(currentGroupId);
        } else {
            showAlert(data.error || 'Error saving requirement', 'danger');
        }
    } catch (error) {
        console.error('Error saving requirement:', error);
        showAlert('Error saving requirement', 'danger');
    }
}

// Requirement details functions
async function showRequirementDetails(requirementId) {
    try {
        const response = await fetch(`/api/requirements/${requirementId}`);
        const data = await response.json();
        
        if (data.success) {
            const req = data.data;
            
            // Populate details tab
            document.getElementById('requirement-details').innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Basic Information</h6>
                        <table class="table table-sm">
                            <tr><td><strong>ID:</strong></td><td>${req.requirement_id}</td></tr>
                            <tr><td><strong>Title:</strong></td><td>${req.title}</td></tr>
                            <tr><td><strong>Description:</strong></td><td>${req.description || '-'}</td></tr>
                            <tr><td><strong>Category:</strong></td><td>${req.category || '-'}</td></tr>
                            <tr><td><strong>Group:</strong></td><td><span class="badge bg-primary">${req.group_name || 'Default'}</span></td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>Status & Priority</h6>
                        <table class="table table-sm">
                            <tr><td><strong>Status:</strong></td><td><span class="badge bg-secondary">${req.status}</span></td></tr>
                            <tr><td><strong>Priority:</strong></td><td><span class="badge priority-${req.priority.toLowerCase()}">${req.priority}</span></td></tr>
                            <tr><td><strong>Created:</strong></td><td>${formatDate(req.created_at)}</td></tr>
                            <tr><td><strong>Updated:</strong></td><td>${formatDate(req.updated_at)}</td></tr>
                        </table>
                    </div>
                </div>
            `;
            
            // Populate history tab
            const historyHtml = req.history.length > 0 ? 
                req.history.map(h => `
                    <div class="history-item">
                        <div class="d-flex justify-content-between">
                            <strong>${h.field_name}</strong>
                            <small class="text-muted">${formatDate(h.changed_at)}</small>
                        </div>
                        <div class="text-muted">Changed by: ${h.changed_by}</div>
                        <div class="mt-1">
                            <span class="text-danger">${h.old_value || 'empty'}</span>
                            <i class="fas fa-arrow-right mx-2"></i>
                            <span class="text-success">${h.new_value || 'empty'}</span>
                        </div>
                    </div>
                `).join('') : 
                '<p class="text-muted">No changes recorded</p>';
            
            document.getElementById('requirement-history').innerHTML = historyHtml;
            
            // Populate relationships tab
            const relationshipsHtml = `
                <div class="row">
                    <div class="col-md-6">
                        <h6>Children (${req.children.length})</h6>
                        ${req.children.length > 0 ? 
                            req.children.map(child => `
                                <div class="tree-node">
                                    <strong>${child.requirement_id}</strong><br>
                                    <small>${child.title}</small>
                                </div>
                            `).join('') : 
                            '<p class="text-muted">No children</p>'
                        }
                    </div>
                    <div class="col-md-6">
                        <h6>Parent</h6>
                        ${req.parent_id ? 
                            `<div class="tree-node">
                                <strong>${req.parent_id}</strong>
                            </div>` : 
                            '<p class="text-muted">No parent</p>'
                        }
                    </div>
                </div>
            `;
            
            document.getElementById('requirement-relationships').innerHTML = relationshipsHtml;
            
            const modal = new bootstrap.Modal(document.getElementById('requirementDetailsModal'));
            modal.show();
        }
    } catch (error) {
        console.error('Error loading requirement details:', error);
        showAlert('Error loading requirement details', 'danger');
    }
}

// Move requirement functions
async function showMoveRequirementModal(requirementId) {
    const requirement = requirementsData.find(r => r.requirement_id === requirementId);
    if (!requirement) return;
    
    // Populate modal
    document.getElementById('move-req-id').value = requirement.requirement_id;
    document.getElementById('move-current-group').value = requirement.group_name || 'Default';
    
    // Load available groups
    try {
        const response = await fetch('/api/groups');
        const data = await response.json();
        
        if (data.success) {
            const groupSelect = document.getElementById('move-new-group');
            groupSelect.innerHTML = '<option value="">Select a group</option>';
            
            function addGroupOptions(groups, level = 0) {
                groups.forEach(group => {
                    if (group.id !== requirement.group_id) { // Don't show current group
                        const indent = '&nbsp;'.repeat(level * 4);
                        const option = document.createElement('option');
                        option.value = group.id;
                        option.innerHTML = indent + group.name;
                        groupSelect.appendChild(option);
                    }
                    
                    if (group.children && group.children.length > 0) {
                        addGroupOptions(group.children, level + 1);
                    }
                });
            }
            
            addGroupOptions(data.data);
        }
    } catch (error) {
        console.error('Error loading groups:', error);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('moveRequirementModal'));
    modal.show();
}

async function moveRequirement() {
    const requirementId = document.getElementById('move-req-id').value;
    const newGroupId = document.getElementById('move-new-group').value;
    
    if (!newGroupId) {
        showAlert('Please select a group', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/requirements/${requirementId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': 'current_user'
            },
            body: JSON.stringify({ group_id: newGroupId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('moveRequirementModal')).hide();
            loadRequirements(currentGroupId);
            loadGroups(); // Refresh groups
        } else {
            showAlert(data.error || 'Error moving requirement', 'danger');
        }
    } catch (error) {
        console.error('Error moving requirement:', error);
        showAlert('Error moving requirement', 'danger');
    }
}

// File upload functions
async function handleFileUpload() {
    const fileInput = document.getElementById('excel-file');
    const file = fileInput.files[0];
    const groupId = document.getElementById('upload-group-id').value;
    if (!file) return;
    if (!groupId) {
        showAlert('Please select a group for the import.', 'warning');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('group_id', groupId);
    try {
        const response = await fetch('/api/upload-excel', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showAlert(`Successfully processed ${data.data.records_processed} requirements`, 'success');
            loadRequirements(currentGroupId); // Refresh requirements list
        } else {
            showAlert(data.error || 'Error uploading file', 'danger');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showAlert('Error uploading file', 'danger');
    }
    fileInput.value = '';
}

// Export functions
async function exportRequirements() {
    try {
        const response = await fetch('/api/export-excel');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `requirements_export_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('Requirements exported successfully', 'success');
        } else {
            showAlert('Error exporting requirements', 'danger');
        }
    } catch (error) {
        console.error('Error exporting requirements:', error);
        showAlert('Error exporting requirements', 'danger');
    }
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Delete function
async function deleteRequirement(requirementId) {
    if (!confirm('Are you sure you want to delete this requirement?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/requirements/${requirementId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Requirement deleted successfully', 'success');
            loadRequirements(currentGroupId);
        } else {
            showAlert(data.error || 'Error deleting requirement', 'danger');
        }
    } catch (error) {
        console.error('Error deleting requirement:', error);
        showAlert('Error deleting requirement', 'danger');
    }
}

async function loadUploadGroupOptions() {
    try {
        const response = await fetch('/api/groups');
        const data = await response.json();
        if (data.success) {
            const groupSelect = document.getElementById('upload-group-id');
            groupSelect.innerHTML = '<option value="">Select a group</option>';
            function addGroupOptions(groups, level = 0) {
                groups.forEach(group => {
                    const indent = '\u00A0'.repeat(level * 4);
                    const option = document.createElement('option');
                    option.value = group.id;
                    option.innerHTML = indent + group.name;
                    groupSelect.appendChild(option);
                    if (group.children && group.children.length > 0) {
                        addGroupOptions(group.children, level + 1);
                    }
                });
            }
            addGroupOptions(data.data);
        }
    } catch (error) {
        console.error('Error loading upload group options:', error);
    }
}

function triggerExcelUpload() {
    document.getElementById('excel-file').click();
}

async function handleExcelFileChange() {
    const fileInput = document.getElementById('excel-file');
    const file = fileInput.files[0];
    if (!file) return;
    if (!currentGroupId) {
        showAlert('Please select a group before uploading requirements.', 'warning');
        fileInput.value = '';
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    formData.append('group_id', currentGroupId);
    try {
        const response = await fetch('/api/upload-excel', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            showAlert(`Successfully processed ${data.data.records_processed} requirements`, 'success');
            loadRequirements(currentGroupId);
        } else {
            showAlert(data.error || 'Error uploading file', 'danger');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showAlert('Error uploading file', 'danger');
    }
    fileInput.value = '';
} 