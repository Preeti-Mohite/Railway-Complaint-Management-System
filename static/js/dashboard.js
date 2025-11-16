// --- Global State ---
const API_URL = 'http://127.0.0.1:8000';
let allComplaints = {}; // A local cache to store all complaints

// --- Authentication & Helpers ---

/**
 * Retrieves the authentication token from browser's local storage.
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Retrieves the logged-in user's info from local storage.
 */
function getAuthUser() {
    const user = localStorage.getItem('authUser');
    return user ? JSON.parse(user) : null;
}

/**
 * Logs the user out by clearing storage and redirecting to the homepage.
 */
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    window.location.href = '/';
}

/**
 * Hides the main details modal.
 */
function hideDetailsModal() {
    document.getElementById('detailsModal').classList.add('hidden');
}

//Formats a Unix timestamp into a readable date string.

function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

/**
 * A wrapper for the fetch API that automatically adds the Authorization header.
 */
async function apiFetch(endpoint, options = {}) {
    const token = getAuthToken();
    if (!token) {
        logout(); // If no token, log out immediately
        throw new Error('Authentication token not found.');
    }

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };

    const response = await fetch(`${API_URL}${endpoint}`, { ...defaultOptions, ...options });

    if (response.status === 401) {
        logout();
        throw new Error('Session expired. Please log in again.');
    }
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An API error occurred.');
    }
    if (response.status === 204) return null;
    return response.json();
}


// --- Main Application Logic ---

document.addEventListener('DOMContentLoaded', () => {
    const user = getAuthUser();
    if (!user) {
        logout();
        return;
    }

    document.getElementById('adminName').textContent = `Welcome, ${user.username}`;
    
    // Add event listeners to filter controls
    document.getElementById('statusFilter').addEventListener('change', renderComplaintsTable);
    document.getElementById('departmentFilter').addEventListener('change', renderComplaintsTable);
    document.getElementById('searchInput').addEventListener('keyup', renderComplaintsTable);

    loadAllComplaints();
});

/**
 * Fetches all complaints and then populates the dashboard.
 */
async function loadAllComplaints() {
    try {
        allComplaints = await apiFetch('/admin/complaints');
        updateStats();
        populateDepartmentFilter();
        renderComplaintsTable();    // Initial render with all data
    } catch (error) {
        console.error('Failed to load complaints:', error);
        alert(error.message);
    }
}

/**
 * Updates the statistic cards at the top of the dashboard.
 */
function updateStats() {
    const complaintsArray = Object.values(allComplaints);
    document.getElementById('totalComplaints').textContent = complaintsArray.length;
    document.getElementById('pendingComplaints').textContent = complaintsArray.filter(c => c.status === 'Pending').length;
    document.getElementById('resolvedComplaints').textContent = complaintsArray.filter(c => c.status === 'Resolved').length;
    document.getElementById('inProgressComplaints').textContent = complaintsArray.filter(c => c.status === 'In Progress').length;
}

/**
 * Dynamically populates the department filter dropdown.
 */
function populateDepartmentFilter() {
    const departments = new Set();
    Object.values(allComplaints).forEach(c => {
        if (c.assigned_departments) {
            c.assigned_departments.forEach(dept => departments.add(dept));
        }
    });

    const filterElement = document.getElementById('departmentFilter');
    filterElement.innerHTML = '<option value="all">All Departments</option>';

    departments.forEach(dept => {
        const option = document.createElement('option');
        option.value = dept;
        option.textContent = dept;
        filterElement.appendChild(option);
    });
}


/**
 * Renders the table based on current filter values.
 */
function renderComplaintsTable() {
    const statusValue = document.getElementById('statusFilter').value;
    const deptValue = document.getElementById('departmentFilter').value;
    const searchValue = document.getElementById('searchInput').value.toLowerCase();

    let complaintsArray = Object.entries(allComplaints);

    // 1. Filter by Status
    if (statusValue !== 'all') {
        complaintsArray = complaintsArray.filter(([id, c]) => c.status === statusValue);
    }

    // 2. Filter by Department
    if (deptValue !== 'all') {
        complaintsArray = complaintsArray.filter(([id, c]) => c.assigned_departments && c.assigned_departments.includes(deptValue));
    }

    // 3. Filter by Search Input (ID or PNR)
    if (searchValue) {
        complaintsArray = complaintsArray.filter(([id, c]) => 
            id.toLowerCase().includes(searchValue) || 
            (c.pnr && c.pnr.toLowerCase().includes(searchValue))
        );
    }

    const tbody = document.getElementById('complaintsTableBody');
    tbody.innerHTML = ''; // Clear existing rows

    const sortedComplaints = complaintsArray.sort(([, a], [, b]) => (b.submitted_at || 0) - (a.submitted_at || 0));

    for (const [id, c] of sortedComplaints) {
        const assignedDepts = c.assigned_departments ? c.assigned_departments.join(', ') : 'N/A';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${id}</td>
            <td>${c.pnr || 'N/A'}</td>
            <td>${formatDate(c.submitted_at)}</td>
            <td>${assignedDepts}</td>
            <td><span class="status-badge ${c.status ? c.status.toLowerCase().replace(' ', '-') : 'unknown'}">${c.status || 'Unknown'}</span></td>
            <td>
                <button class="action-btn" onclick="viewComplaintDetails('${id}')">View/Update</button>
            </td>
        `;
        tbody.appendChild(tr);
    }
}

/**
 * Shows the modal with details for a specific complaint.
 */
function viewComplaintDetails(complaintId) {
    const complaint = allComplaints[complaintId];
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    modalTitle.textContent = `Details for Complaint #${complaintId}`;
    const predictedText = complaint.predicted ? complaint.predicted.map(p => `${p.department} (${(p.score*100).toFixed(1)}%)`).join(', ') : 'N/A';

    modalBody.innerHTML = `
        <div class="detail-group">
            <span class="detail-label">Full Complaint:</span>
            <span class="detail-value">${complaint.complaint || 'N/A'}</span>
        </div>
        <div class="detail-group">
            <span class="detail-label">AI Predicted:</span>
            <span class="detail-value">${predictedText}</span>
        </div>
        <hr>
        <form id="updateForm" class="update-form">
            <input type="hidden" id="updateComplaintId" value="${complaintId}">
            <div class="form-group">
                <label for="newStatus">Update Status</label>
                <select id="newStatus" required>
                    <option value="Pending" ${complaint.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="In Progress" ${complaint.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Resolved" ${complaint.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                </select>
            </div>
            <div class="form-group">
                <label for="newDepartments">Re-assign Departments (comma-separated)</label>
                <input type="text" id="newDepartments" value="${complaint.assigned_departments ? complaint.assigned_departments.join(', ') : ''}">
            </div>
            <button type="submit" class="update-btn">Save Changes</button>
        </form>
    `;

    document.getElementById('updateForm').addEventListener('submit', handleUpdateSubmission);
    document.getElementById('detailsModal').classList.remove('hidden');
}

/**
 * Handles the submission of the update form inside the modal.
 */
async function handleUpdateSubmission(e) {
    e.preventDefault();
    const complaintId = document.getElementById('updateComplaintId').value;
    const newStatus = document.getElementById('newStatus').value;
    const newDepartments = document.getElementById('newDepartments').value;

    try {
        await apiFetch(`/admin/update/${complaintId}?status=${newStatus}&departments=${newDepartments}`, {
            method: 'POST'
        });
        alert('Complaint updated successfully!');
        hideDetailsModal();
        loadAllComplaints(); // Refresh everything after an update
    } catch (error) {
        console.error('Update failed:', error);
        alert(error.message);
    }
}

