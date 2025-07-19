// Global variables
let currentRequirementId = null;
let requirementsData = [];
let groupsData = [];
let selectedRequirements = new Set(); // Track selected requirements for batch editing

// EasyMDE instance for requirement modal
let reqDescriptionMDE = null;

function initReqDescriptionMDE() {
    // Wait for the modal to be fully shown
    setTimeout(() => {
        const editorDiv = document.getElementById('req-description-editor');
        if (!editorDiv) {
            console.error('req-description-editor div not found');
            return;
        }
        
        // Clear any existing content
        editorDiv.innerHTML = '';
        
        // Create a textarea element for EasyMDE
        const textarea = document.createElement('textarea');
        textarea.id = 'req-description-textarea';
        editorDiv.appendChild(textarea);
        
        // Initialize EasyMDE
        reqDescriptionMDE = new EasyMDE({
            element: textarea,
            autoDownloadFontAwesome: false,
            spellChecker: false,
            status: false,
            minHeight: '100px',
            maxHeight: '300px',
            toolbar: ["bold", "italic", "heading", "|", "quote", "unordered-list", "ordered-list", "|", "link", "preview", "guide"]
        });
    }, 100);
}

function setReqDescriptionValue(value) {
    if (!reqDescriptionMDE) {
        // If EasyMDE is not initialized, set the value after initialization
        setTimeout(() => {
            if (reqDescriptionMDE) {
                reqDescriptionMDE.value(value || '');
            }
        }, 200);
        return;
    }
    reqDescriptionMDE.value(value || '');
}

function getReqDescriptionValue() {
    if (!reqDescriptionMDE) return '';
    return reqDescriptionMDE.value();
}

function destroyReqDescriptionMDE() {
    if (reqDescriptionMDE) {
        reqDescriptionMDE.toTextArea();
        reqDescriptionMDE = null;
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    loadDashboard();
    setupEventListeners();
    loadGroups(); // Ensure groupsData is loaded on page load
    loadUploadGroupOptions();
    enableTableColumnResizing();
});

function enableTableColumnResizing() {
    const table = document.querySelector('table');
    if (!table) return;
    const ths = table.querySelectorAll('th');
    let startX, startWidth, colIndex, resizing = false;

    ths.forEach((th, i) => {
        const handle = th.querySelector('.resize-handle');
        if (!handle) return; // Skip columns without resize handles (like checkbox column)
        handle.addEventListener('mousedown', function(e) {
            e.preventDefault();
            e.stopPropagation();
            startX = e.pageX;
            startWidth = th.offsetWidth;
            colIndex = i;
            resizing = true;
            document.body.style.cursor = 'col-resize';
        });
    });

    document.addEventListener('mousemove', function(e) {
        if (!resizing) return;
        const dx = e.pageX - startX;
        const newWidth = Math.max(80, startWidth + dx);
        const table = document.querySelector('table');
        if (!table) return;
        const th = table.querySelectorAll('th')[colIndex];
        th.style.minWidth = newWidth + 'px';
        th.style.width = newWidth + 'px';
        // Set width for all tds in this column
        table.querySelectorAll('tr').forEach(row => {
            const cell = row.children[colIndex];
            if (cell) {
                cell.style.minWidth = newWidth + 'px';
                cell.style.width = newWidth + 'px';
            }
        });
    });

    document.addEventListener('mouseup', function() {
        if (resizing) {
            resizing = false;
            document.body.style.cursor = '';
        }
    });
}

// User authentication functions
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/user/current');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('current-user').textContent = data.user.username;
        } else {
            // Redirect to login if not authenticated
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
        window.location.href = '/login';
    }
}

async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error during logout:', error);
        window.location.href = '/login';
    }
}

// Setup event listeners
function setupEventListeners() {
    // File upload - only if elements exist
    const fileInput = document.getElementById('excel-file');
    const uploadArea = document.getElementById('upload-area');
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    
    if (uploadArea) {
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
            if (files.length > 0 && fileInput) {
                fileInput.files = files;
                handleFileUpload();
            }
        });
    }
    
    // Search and filters - only if elements exist
    const searchInput = document.getElementById('search-input');
    const statusFilter = document.getElementById('status-filter');
    const chapterFilter = document.getElementById('chapter-filter');
    const groupFilter = document.getElementById('group-filter');
    
    if (searchInput) {
        searchInput.addEventListener('input', filterRequirements);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', filterRequirements);
    }
    if (chapterFilter) {
        chapterFilter.addEventListener('change', filterRequirements);
    }
    if (groupFilter) {
        groupFilter.addEventListener('change', filterRequirements);
    }
    
    // Modal cleanup for EasyMDE
    const requirementModal = document.getElementById('requirementModal');
    if (requirementModal) {
        requirementModal.addEventListener('hidden.bs.modal', function() {
            // Destroy EasyMDE when modal is hidden
            destroyReqDescriptionMDE();
        });
    }
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
        case 'graph':
            loadGraph();
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
            document.getElementById('in-progress-requirements').textContent = 
                requirements.filter(r => r.status === 'In Progress').length;
            

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
            loadGroupOptions();
            populateGroupFilter(); // Ensure group filter is populated after groupsData is set
        }
    } catch (error) {
        console.error('Error loading groups:', error);
        showAlert('Error loading groups', 'danger');
    }
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
    // Clear any edit state
    document.getElementById('groupModal').removeAttribute('data-edit-group-id');
    loadGroupOptions();
    
    const modal = new bootstrap.Modal(document.getElementById('groupModal'));
    modal.show();
}

function editGroup(groupId) {
    // Find the group in the groupsData
    function findGroup(groups, id) {
        for (let group of groups) {
            if (group.id === id) {
                return group;
            }
            if (group.children && group.children.length > 0) {
                const found = findGroup(group.children, id);
                if (found) return found;
            }
        }
        return null;
    }
    
    const group = findGroup(groupsData, groupId);
    if (!group) {
        showAlert('Group not found', 'danger');
        return;
    }
    
    // Set modal title and populate form
    document.getElementById('group-modal-title').textContent = 'Edit Group';
    document.getElementById('group-name').value = group.name;
    document.getElementById('group-description').value = group.description || '';
    
    // Load group options and set parent
    loadGroupOptions();
    if (group.parent_id) {
        document.getElementById('group-parent-id').value = group.parent_id;
    } else {
        document.getElementById('group-parent-id').value = '';
    }
    
    // Store the group ID for editing
    document.getElementById('groupModal').setAttribute('data-edit-group-id', groupId);
    
    const modal = new bootstrap.Modal(document.getElementById('groupModal'));
    modal.show();
}

async function saveGroup() {
    const formData = {
        name: document.getElementById('group-name').value,
        description: document.getElementById('group-description').value,
        parent_id: document.getElementById('group-parent-id').value || null
    };
    
    const editGroupId = document.getElementById('groupModal').getAttribute('data-edit-group-id');
    const isEditing = editGroupId !== null;
    
    try {
        const url = isEditing ? `/api/groups/${editGroupId}` : '/api/groups';
        const method = isEditing ? 'PUT' : 'POST';
        
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
            showAlert(isEditing ? 'Group updated successfully' : 'Group created successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('groupModal')).hide();
            // Clear the edit group ID
            document.getElementById('groupModal').removeAttribute('data-edit-group-id');
            loadGroups();
        } else {
            showAlert(data.error || (isEditing ? 'Error updating group' : 'Error creating group'), 'danger');
        }
    } catch (error) {
        console.error(isEditing ? 'Error updating group:' : 'Error creating group:', error);
        showAlert(isEditing ? 'Error updating group' : 'Error creating group', 'danger');
    }
}

async function deleteGroup(groupId) {
    if (!confirm('Are you sure you want to delete this group? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/groups/${groupId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': 'current_user'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Group deleted successfully', 'success');
            loadGroups();
        } else {
            showAlert(data.error || 'Error deleting group', 'danger');
        }
    } catch (error) {
        console.error('Error deleting group:', error);
        showAlert('Error deleting group', 'danger');
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
            populateChapterFilter();
            populateGroupFilter();
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
            <td><input type="checkbox" class="form-check-input requirement-checkbox" value="${req.requirement_id}" ${selectedRequirements.has(req.requirement_id) ? 'checked' : ''} onchange="handleRequirementSelection(event, '${req.requirement_id}')" onclick="event.stopPropagation();"></td>
            <td>${req.requirement_id}</td>
            <td>${req.title}</td>
            <td>${req.description ? marked.parse(req.description) : ''}</td>
            <td><span class="badge bg-secondary">${req.status}</span></td>
            <td>${req.chapter || '-'}</td>
            <td>${req.group_name || '-'}</td>
            <td>${req.children_count}</td>
            <td>${formatDate(req.updated_at)}</td>
            <td>
                <button class="btn btn-sm btn-primary me-1" onclick="event.stopPropagation(); editRequirement('${req.requirement_id}')"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteRequirement('${req.requirement_id}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(row);
    });
    updateBatchEditButton();
}

function filterRequirements() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    const chapterFilter = document.getElementById('chapter-filter').value;
    const groupFilter = document.getElementById('group-filter').value;
    
    const filtered = requirementsData.filter(req => {
        // Text search
        const matchesSearch = !searchTerm || 
            req.title.toLowerCase().includes(searchTerm) ||
            req.requirement_id.toLowerCase().includes(searchTerm) ||
            (req.description && req.description.toLowerCase().includes(searchTerm));
        
        // Status filter
        const matchesStatus = !statusFilter || req.status === statusFilter;
        
        // Chapter filter
        const matchesChapter = !chapterFilter || req.chapter === chapterFilter;
        
        // Group filter (compare as strings)
        const matchesGroup = !groupFilter || String(req.group_id) === String(groupFilter);
        
        return matchesSearch && matchesStatus && matchesChapter && matchesGroup;
    });
    
    renderRequirementsTable(filtered);
    populateGroupFilter(); // Ensure filter is up to date
}

function clearFilters() {
    document.getElementById('search-input').value = '';
    document.getElementById('status-filter').value = '';
    document.getElementById('chapter-filter').value = '';
    document.getElementById('group-filter').value = '';
    filterRequirements();
}

// Add populateChapterFilter and populateGroupFilter
function populateChapterFilter() {
    const chapterSelect = document.getElementById('chapter-filter');
    const chapters = [...new Set(requirementsData.map(req => req.chapter).filter(ch => ch))];
    chapterSelect.innerHTML = '<option value="">All Chapters</option>';
    chapters.forEach(chapter => {
        const option = document.createElement('option');
        option.value = chapter;
        option.textContent = chapter;
        chapterSelect.appendChild(option);
    });
}
function populateGroupFilter() {
    const groupSelect = document.getElementById('group-filter');
    const groups = [...new Set(requirementsData.map(req => req.group_id).filter(gid => gid))];
    groupSelect.innerHTML = '<option value="">All Groups</option>';
    groups.forEach(gid => {
        const group = groupsData.find(g => String(g.id) === String(gid));
        const option = document.createElement('option');
        option.value = gid;
        option.textContent = group ? group.name : gid;
        groupSelect.appendChild(option);
    });
}


// Modal functions
function showAddRequirementModal() {
    document.getElementById('modal-title').textContent = 'Add Requirement';
    document.getElementById('requirement-form').reset();
    currentRequirementId = null;
    // Load parent options
    loadGroupOptions();
    setReqDescriptionValue('');
    
    const modal = new bootstrap.Modal(document.getElementById('requirementModal'));
    modal.show();
    
    // Initialize EasyMDE after modal is shown
    initReqDescriptionMDE();
}

function editRequirement(requirementId) {
    const requirement = requirementsData.find(r => r.requirement_id === requirementId);
    if (!requirement) return;
    document.getElementById('modal-title').textContent = 'Edit Requirement';
    currentRequirementId = requirementId;
    // Populate form
    document.getElementById('req-id').value = requirement.requirement_id;
    document.getElementById('req-title').value = requirement.title;
    document.getElementById('req-status').value = requirement.status;
    loadGroupOptions();
    if (requirement.group_id) {
        document.getElementById('req-group-id').value = requirement.group_id;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('requirementModal'));
    modal.show();
    
    // Initialize EasyMDE after modal is shown and set the value
    initReqDescriptionMDE();
    setReqDescriptionValue(requirement.description || '');
}

async function saveRequirement() {
    const formData = {
        requirement_id: document.getElementById('req-id').value,
        title: document.getElementById('req-title').value,
        description: getReqDescriptionValue(),
        status: document.getElementById('req-status').value,
        chapter: document.getElementById('chapter-field').value || null
    };
    const groupId = document.getElementById('req-group-id').value;
    if (groupId) {
        formData.group_id = groupId;
    }
    console.log('saveRequirement called, formData:', formData);
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
        console.log('saveRequirement response:', data);
        if (data.success) {
            showAlert('Requirement saved successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('requirementModal')).hide();
            loadRequirements();
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
                        <div class="detail-section">
                            <h6>Basic Information</h6>
                            <div class="detail-item">
                                <div class="detail-label">ID:</div>
                                <div class="detail-value">${req.requirement_id}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Title:</div>
                                <div class="detail-value">${req.title}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Group:</div>
                                <div class="detail-value">${req.group_name || 'Default'}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="detail-section">
                            <h6>Status & Timeline</h6>
                            <div class="detail-item">
                                <div class="detail-label">Status:</div>
                                <div class="detail-value"><span class="badge bg-secondary">${req.status}</span></div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Created:</div>
                                <div class="detail-value">${formatDate(req.created_at)}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-label">Updated:</div>
                                <div class="detail-value">${formatDate(req.updated_at)}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="detail-section">
                            <h6>Description</h6>
                            <div class="detail-item-full">
                                <div class="detail-value-full">${req.description ? marked.parse(req.description) : '-'}</div>
                            </div>
                        </div>
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
                        <h6>Parents (${req.parent_objs.length})</h6>
                        ${req.parent_objs.length > 0 ?
                            req.parent_objs.map(parent => `
                                <div class="tree-node">
                                    <strong>${parent.requirement_id}</strong><br>
                                    <small>${parent.title}</small>
                                </div>
                            `).join('') :
                            '<p class="text-muted">No parent</p>'
                        }
                    </div>
                </div>
            `;
            
            document.getElementById('requirement-relationships').innerHTML = relationshipsHtml;
            
            // Initialize tabs properly
            const tabElements = document.querySelectorAll('#requirement-tabs .nav-link');
            tabElements.forEach(tab => {
                tab.addEventListener('click', function(e) {
                    e.preventDefault();
                    // Remove active class from all tabs and panes
                    document.querySelectorAll('#requirement-tabs .nav-link').forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.tab-pane').forEach(p => {
                        p.classList.remove('active', 'show');
                    });
                    
                    // Add active class to clicked tab
                    this.classList.add('active');
                    
                    // Show corresponding pane
                    const targetId = this.getAttribute('href').substring(1);
                    const targetPane = document.getElementById(targetId);
                    if (targetPane) {
                        targetPane.classList.add('active', 'show');
                    }
                });
            });
            
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
            loadRequirements(); // Changed from loadRequirements(currentGroupId)
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
            loadRequirements(); // Refresh requirements list
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
    
    // Format: dd.mm.yyyy hh:mm:ss
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${day}.${month}.${year} ${hours}:${minutes}:${seconds}`;
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
            loadRequirements(); // Changed from loadRequirements(currentGroupId)
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
            const groupSelect = document.getElementById('excel-upload-group');
            if (!groupSelect) return; // Null check
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



// Batch editing functions
function handleRequirementSelection(event, requirementId) {
    event.stopPropagation();
    
    if (event.target.checked) {
        selectedRequirements.add(requirementId);
    } else {
        selectedRequirements.delete(requirementId);
    }
    
    updateBatchEditButton();
}

function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const requirementCheckboxes = document.querySelectorAll('.requirement-checkbox');
    
    requirementCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
        if (selectAllCheckbox.checked) {
            selectedRequirements.add(checkbox.value);
        } else {
            selectedRequirements.delete(checkbox.value);
        }
    });
    
    updateBatchEditButton();
}

function updateBatchEditButton() {
    const batchEditBtn = document.getElementById('batch-edit-btn');
    const selectedCount = document.getElementById('selected-count');
    const count = selectedRequirements.size;
    
    selectedCount.textContent = count;
    
    if (count > 0) {
        batchEditBtn.style.display = 'inline-block';
    } else {
        batchEditBtn.style.display = 'none';
    }
}

function showBatchEditModal() {
    const selectedCount = document.getElementById('batch-selected-count');
    const selectedList = document.getElementById('batch-selected-list');
    
    selectedCount.textContent = selectedRequirements.size;
    
    // Populate selected requirements list
    const selectedReqs = Array.from(selectedRequirements).map(id => {
        const req = requirementsData.find(r => r.requirement_id === id);
        return req ? `${req.requirement_id} - ${req.title}` : id;
    });
    
    selectedList.innerHTML = selectedReqs.map(req => `<div class="small text-muted">${req}</div>`).join('');
    
    // Reset form
    document.getElementById('batch-edit-form').reset();
    
    // Load group options
    const batchGroupSelect = document.getElementById('batch-group-id');
    batchGroupSelect.innerHTML = '<option value="">Keep Current</option>';
    
    function addGroupOptions(groups, level = 0) {
        groups.forEach(group => {
            const indent = '&nbsp;'.repeat(level * 4);
            const option = document.createElement('option');
            option.value = group.id;
            option.innerHTML = `${indent}${group.name}`;
            batchGroupSelect.appendChild(option);
            
            if (group.children && group.children.length > 0) {
                addGroupOptions(group.children, level + 1);
            }
        });
    }
    
    addGroupOptions(groupsData);
    
    const modal = new bootstrap.Modal(document.getElementById('batchEditModal'));
    modal.show();
}

async function saveBatchEdit() {
    const status = document.getElementById('batch-status').value;
    const chapter = document.getElementById('batch-chapter').value;
    const groupId = document.getElementById('batch-group-id').value;
    
    // Prepare update data
    const updateData = {};
    if (status) updateData.status = status;
    if (chapter !== '') updateData.chapter = chapter || null; // Allow empty string to clear chapter
    if (groupId) updateData.group_id = groupId;
    
    if (Object.keys(updateData).length === 0) {
        showAlert('Please select at least one field to update', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/requirements/batch-update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': 'current_user'
            },
            body: JSON.stringify({
                requirement_ids: Array.from(selectedRequirements),
                updates: updateData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Successfully updated ${data.updated_count} requirements`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('batchEditModal')).hide();
            
            // Clear selections
            selectedRequirements.clear();
            document.getElementById('select-all-checkbox').checked = false;
            
            // Reload data
            loadRequirements(); // Changed from loadRequirements(currentGroupId)
            loadDashboard();
        } else {
            showAlert(data.error || 'Error updating requirements', 'danger');
        }
    } catch (error) {
        console.error('Error updating requirements:', error);
        showAlert('Error updating requirements', 'danger');
    }
} 

// Excel Upload Modal Logic
function showExcelUploadModal() {
    // Reset modal state
    document.getElementById('excel-upload-file').value = '';
    document.getElementById('excel-upload-filename').textContent = '';
    document.getElementById('add-group-inline').style.display = 'none';
    document.getElementById('new-group-name').value = '';
    // Populate group dropdown
    populateExcelUploadGroupDropdown();
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('excelUploadModal'));
    modal.show();
}

function populateExcelUploadGroupDropdown() {
    const groupSelect = document.getElementById('excel-upload-group');
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
    addGroupOptions(groupsData);
}

// Drag-and-drop and file selection
const excelUploadArea = document.getElementById('excel-upload-area');
if (excelUploadArea) {
    excelUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        excelUploadArea.style.borderColor = '#667eea';
    });
    excelUploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        excelUploadArea.style.borderColor = '#dee2e6';
    });
    excelUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        excelUploadArea.style.borderColor = '#dee2e6';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('excel-upload-file').files = files;
            document.getElementById('excel-upload-filename').textContent = files[0].name;
        }
    });
    document.getElementById('excel-upload-file').addEventListener('change', function() {
        if (this.files.length > 0) {
            document.getElementById('excel-upload-filename').textContent = this.files[0].name;
        } else {
            document.getElementById('excel-upload-filename').textContent = '';
        }
    });
}

function showAddGroupInline() {
    document.getElementById('add-group-inline').style.display = 'block';
    document.getElementById('new-group-name').focus();
}
function hideAddGroupInline() {
    document.getElementById('add-group-inline').style.display = 'none';
    document.getElementById('new-group-name').value = '';
}
async function addGroupInline() {
    const name = document.getElementById('new-group-name').value.trim();
    if (!name) {
        showAlert('Group name cannot be empty', 'warning');
        return;
    }
    try {
        const response = await fetch('/api/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-User-ID': 'current_user' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        if (data.success) {
            showAlert('Group created successfully', 'success');
            hideAddGroupInline();
            await loadGroups(); // refresh groupsData
            populateExcelUploadGroupDropdown();
            document.getElementById('excel-upload-group').value = data.data.id;
        } else {
            showAlert(data.error || 'Error creating group', 'danger');
        }
    } catch (error) {
        showAlert('Error creating group', 'danger');
    }
}

async function handleExcelUploadModal() {
    const fileInput = document.getElementById('excel-upload-file');
    const groupId = document.getElementById('excel-upload-group').value;
    if (!fileInput.files.length) {
        showAlert('Please select an Excel file to upload.', 'warning');
        return;
    }
    if (!groupId) {
        showAlert('Please select a group for import.', 'warning');
        return;
    }
    const file = fileInput.files[0];
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
            showAlert('Excel file uploaded successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('excelUploadModal')).hide();
            loadRequirements();
            loadDashboard();
        } else {
            showAlert(data.error || 'Error uploading file', 'danger');
        }
    } catch (error) {
        showAlert('Error uploading file', 'danger');
    }
    fileInput.value = '';
    document.getElementById('excel-upload-filename').textContent = '';
} 

// Graph Visualization using Vis.js
let network = null;
let graphData = { nodes: [], edges: [] };
let selectedNode = null;
let isCtrlPressed = false;
let selectedRequirementId = null; // Store requirement_id for parent-child logic
let selectedNodeHighlight = null; // Store Vis.js nodeId for highlight
let selectedEdge = null; // Track selected edge for deletion

// Register Delete key event handler ONCE for edge deletion after DOM is loaded
window.addEventListener('DOMContentLoaded', function() {
    if (!window._deleteEdgeHandlerRegistered) {
        document.addEventListener('keydown', async function(e) {
            if (e.key === 'Delete' && selectedEdge) {
                // Find parent and child requirement_id from node IDs
                const parentNode = graphData.nodes.find(n => n.id === selectedEdge.from);
                const childNode = graphData.nodes.find(n => n.id === selectedEdge.to);
                if (parentNode && childNode) {
                    await removeParentChildLink(parentNode.requirement_id, childNode.requirement_id);
                    selectedEdge = null;
                }
            }
        });
        window._deleteEdgeHandlerRegistered = true;
    }
});

// Graph functions
async function loadGraph() {
    try {
        const response = await fetch('/api/requirements/graph');
        const data = await response.json();
        
        if (data.success) {
            graphData = data.data;
            initializeGraph();
        } else {
            showAlert(data.error || 'Error loading graph data', 'danger');
        }
    } catch (error) {
        console.error('Error loading graph:', error);
        showAlert('Error loading graph data', 'danger');
    }
}

function initializeGraph() {
    const container = document.getElementById('graph-container');
    if (!container) return;
    
    // Clear existing network
    if (network) {
        network.destroy();
    }
    
    // Create nodes dataset
    const nodes = new vis.DataSet(graphData.nodes.map(node => {
        const nodeData = {
            ...node,
            shape: 'box',
            font: {
                size: 12,
                face: 'Arial'
            },
            borderWidth: 2,
            shadow: true,
            margin: 10
        };
        if (typeof node.x === 'number' && typeof node.y === 'number') {
            nodeData.x = node.x;
            nodeData.y = node.y;
            nodeData.fixed = { x: false, y: false };
        }
        return nodeData;
    }));
    
    // Create edges dataset
    const edges = new vis.DataSet(graphData.edges);
    
    // Network options
    const options = {
        nodes: {
            shape: 'box',
            font: {
                size: 12,
                face: 'Arial'
            },
            borderWidth: 2,
            shadow: true,
            margin: 10
        },
        edges: {
            width: 2,
            color: { color: '#666', highlight: '#007bff' },
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'none'
            }
        },
        physics: {
            enabled: false  // Physics disabled permanently
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true
        }
    };
    
    // Create network
    network = new vis.Network(container, { nodes, edges }, options);
    
    // Save node position on drag end
    network.on('dragEnd', function(params) {
        // console.log('dragEnd event fired:', params);
        if (params.nodes && params.nodes.length > 0) {
            // Get all positions at once
            const positions = network.getPositions(params.nodes);
            params.nodes.forEach(nodeId => {
                const node = nodes.get(nodeId);
                const req = graphData.nodes.find(n => n.id === nodeId || n.id == node.id);
                const pos = positions[nodeId];
                // console.log('Node after drag:', node);
                // console.log('Mapped requirement for node:', req);
                // console.log('Position from network:', pos);
                if (pos && req && req.requirement_id) {
                    // console.log('Saving position for requirement:', req.requirement_id, pos.x, pos.y);
                    saveNodePosition(req.requirement_id, pos.x, pos.y);
                } else {
                    // console.warn('Could not map node to requirement or missing coordinates:', node, req, pos);
                }
            });
        }
    });
    
    // Event listeners
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            if (isCtrlPressed) {
                if (selectedRequirementId && selectedRequirementId !== node.requirement_id) {
                    // Second node selected, trigger relationship
                    console.log('Ctrl+click: parent requirement_id:', selectedRequirementId, 'child requirement_id:', node.requirement_id);
                    handleParentChildRelationship(selectedRequirementId, node.requirement_id);
                    // Remove highlight from first node
                    if (selectedNodeHighlight) {
                        network.body.nodes[selectedNodeHighlight].setOptions({ color: undefined });
                        selectedNodeHighlight = null;
                    }
                    selectedRequirementId = null;
                } else {
                    // First node selected or same node clicked again
                    selectedRequirementId = node.requirement_id;
                    // Debug: log first node selection
                    console.log('Ctrl+click: first node selected, requirement_id:', node.requirement_id);
                    // Highlight the selected node
                    if (selectedNodeHighlight) {
                        network.body.nodes[selectedNodeHighlight].setOptions({ color: undefined });
                    }
                    network.body.nodes[nodeId].setOptions({ color: { background: '#ffe066' } });
                    selectedNodeHighlight = nodeId;
                }
                // Suppress details modal when Ctrl is pressed
                return;
            } else {
                // Show requirement details
                showRequirementDetails(node.requirement_id);
                // Remove highlight if any
                if (selectedNodeHighlight) {
                    network.body.nodes[selectedNodeHighlight].setOptions({ color: undefined });
                    selectedNodeHighlight = null;
                }
                selectedRequirementId = null;
            }
        }
    });
    
    network.on('doubleClick', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = nodes.get(nodeId);
            showRequirementDetails(node.requirement_id);
        }
    });
    
    // Handle Ctrl key for parent-child relationship creation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Control') {
            isCtrlPressed = true;
        }
    });
    
    document.addEventListener('keyup', function(e) {
        if (e.key === 'Control') {
            isCtrlPressed = false;
        }
    });
    
    // Handle node selection for parent-child relationships
    network.on('select', function(params) {
        if (params.nodes.length > 0 && isCtrlPressed) {
            selectedNode = params.nodes[0];
        }
    });
    
    // Track selected edge
    network.on('selectEdge', function(params) {
        if (params.edges.length > 0) {
            selectedEdge = edges.get(params.edges[0]);
            console.log('Selected edge:', selectedEdge);
        } else {
            selectedEdge = null;
        }
    });
    network.on('deselectEdge', function() {
        selectedEdge = null;
    });
}

async function handleParentChildRelationship(parentRequirementId, childRequirementId) {
    try {
        const parentNode = graphData.nodes.find(n => n.requirement_id === parentRequirementId);
        const childNode = graphData.nodes.find(n => n.requirement_id === childRequirementId);
        
        if (!parentNode || !childNode) {
            showAlert('Invalid node selection', 'warning');
            console.log('Invalid node selection:', { parentRequirementId, childRequirementId, parentNode, childNode });
            return;
        }
        // Check if relationship already exists
        const existingEdge = graphData.edges.find(e => e.from === parentNode.id && e.to === childNode.id);
        if (existingEdge) {
            // Debug: log removal payload
            console.log('Removing parent-child relationship:', { childRequirementId, parent_id: null });
            const response = await fetch(`/api/requirements/${childRequirementId}/parent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parent_id: null })
            });
            const data = await response.json();
            console.log('Backend response (remove relationship):', data);
            if (data.success) {
                showAlert('Parent-child relationship removed', 'success');
                await loadGraph(); // Refresh graph
            } else {
                showAlert(data.error || 'Error removing relationship', 'danger');
            }
        } else {
            // Debug: log creation payload
            console.log('Creating parent-child relationship:', { childRequirementId, parent_id: parentRequirementId });
            const response = await fetch(`/api/requirements/${childRequirementId}/parent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parent_id: parentRequirementId })
            });
            const data = await response.json();
            console.log('Backend response (create relationship):', data);
            if (data.success) {
                showAlert('Parent-child relationship created', 'success');
                await loadGraph(); // Refresh graph
            } else {
                showAlert(data.error || 'Error creating relationship', 'danger');
            }
        }
    } catch (error) {
        console.error('Error handling parent-child relationship:', error);
        showAlert('Error updating relationship', 'danger');
    }
}

async function removeParentChildLink(parentRequirementId, childRequirementId) {
    try {
        // Custom endpoint: remove only this parent-child link
        const response = await fetch(`/api/requirements/${childRequirementId}/parent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ parent_id: parentRequirementId, remove_only: true })
        });
        const data = await response.json();
        if (data.success) {
            showAlert('Parent-child relationship deleted', 'success');
            await loadGraph();
        } else {
            showAlert(data.error || 'Error deleting relationship', 'danger');
            // Do not refresh the graph if deletion failed
        }
    } catch (error) {
        console.error('Error deleting parent-child relationship:', error);
        showAlert('Error deleting relationship', 'danger');
    }
}

function refreshGraph() {
    loadGraph();
}

function fitGraph() {
    if (network) {
        network.fit();
    }
}

async function saveNodePosition(requirementId, x, y) {
    try {
        const response = await fetch(`/api/requirements/${requirementId}/position`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ x, y })
        });
        
        const data = await response.json();
        if (!data.success) {
            console.error('Error saving position:', data.error);
        }
    } catch (error) {
        console.error('Error saving node position:', error);
    }
}

 
