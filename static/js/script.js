// --- Constants ---
const API_URL = 'http://127.0.0.1:8000';

// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    const complaintForm = document.getElementById('complaintForm');
    if (complaintForm) complaintForm.addEventListener('submit', handleComplaintSubmission);

    const adminLoginForm = document.getElementById('adminLoginForm');
    if (adminLoginForm) adminLoginForm.addEventListener('submit', handleAdminLogin);
});


// --- Complaint Submission ---
async function handleComplaintSubmission(e) {
    e.preventDefault();
    const pnr = document.getElementById('pnr').value;
    const complaintText = document.getElementById('complaint').value;
    const submitBtn = e.target.querySelector('.submit-btn');

    const payload = { pnr, complaint: complaintText };
    toggleButtonLoading(submitBtn, true, 'Submitting...');

    try {
        const response = await fetch(`${API_URL}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Submission failed');
        
        displayComplaintResult(result);
        e.target.reset();
    } catch (error) {
        console.error('Submission Error:', error);
        alert(`Error: ${error.message}`);
    } finally {
        toggleButtonLoading(submitBtn, false, 'Submit Complaint');
    }
}

// --- Staff Login ---
async function handleAdminLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = e.target.querySelector('.login-btn');

    toggleButtonLoading(loginBtn, true, 'Logging In...');

    try {
        const response = await fetch(`${API_URL}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const result = await response.json();
        if (!response.ok) {
            // Use the detailed error message from the server
            throw new Error(result.detail || 'Login failed');
        }

        // Correctly save the auth token and the entire 'user' object
        // This is crucial for the dashboard to work properly.
        localStorage.setItem('authToken', result.access_token);
        localStorage.setItem('authUser', JSON.stringify(result.user));
        
        // Redirect to the dashboard page
        window.location.href = '/admin/dashboard';

    } catch (error) {
        console.error('Login Error:', error);
        // Display the specific error message to the user
        alert(`Login Failed: ${error.message}`);
    } finally {
        toggleButtonLoading(loginBtn, false, 'Login');
    }
}

// --- Status Check ---
async function checkStatus() {
    const complaintId = document.getElementById('statusComplaintId').value.trim();
    if (!complaintId) return alert('Please enter a Complaint ID.');

    const statusDetailsDiv = document.getElementById('statusDetails');
    statusDetailsDiv.innerHTML = '<div class="loading-small"></div>'; 
    try {
        const response = await fetch(`${API_URL}/status/${complaintId}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Complaint not found');

        statusDetailsDiv.innerHTML = `
            <div class="detail-group">
                <span class="detail-label">Status:</span> 
                <span class="detail-value"><span class="status-badge ${data.status.toLowerCase()}">${data.status}</span></span>
            </div>
            <div class="detail-group">
                <span class="detail-label">Assigned:</span> 
                <span class="detail-value">${(data.assigned_departments || []).join(', ')}</span>
            </div>
        `;
    } catch (error) {
        console.error('Status Check Error:', error);
        statusDetailsDiv.innerHTML = `<p class="error-text">${error.message}</p>`;
    } finally {
        document.getElementById('statusResult').classList.remove('hidden');
    }
}

// --- UI Helper Functions ---
function showAdminLogin() { document.getElementById('adminLoginModal').classList.remove('hidden'); }
function hideAdminLogin() { document.getElementById('adminLoginModal').classList.add('hidden'); }

function displayComplaintResult(result) {
    document.getElementById('complaintId').textContent = result.complaint_id;
    // Safely access the predicted department
    const department = result.predicted?.[0]?.department || 'N/A';
    document.getElementById('assignedDepartment').textContent = department;
    document.getElementById('departmentResult').classList.remove('hidden');
}

function toggleButtonLoading(button, isLoading, text) {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = `<div class="loading"></div> ${text}`;
    } else {
        button.disabled = false;
        button.innerHTML = text;
    }
}