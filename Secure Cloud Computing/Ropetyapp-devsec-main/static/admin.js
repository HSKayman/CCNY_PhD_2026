// Admin Dashboard JavaScript

let allUsers = [];
let allBookings = [];
let totalRobotCount = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    loadAllData();
    setupAlertForm();
    initAdminPasswordChangeHandlers();
    
    // Auto-refresh every 30 seconds
    setInterval(loadAllData, 30000);
});

// Tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Remove active class from all
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked
            btn.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // Load data for the active tab
            if (targetTab === 'bookings') {
                loadBookings();
            } else if (targetTab === 'users') {
                loadUsers();
            } else if (targetTab === 'monitoring') {
                loadMonitoring();
            } else if (targetTab === 'chat') {
                loadChatConversations();
            } else if (targetTab === 'announcements') {
                loadAnnouncementsAdmin();
            } else if (targetTab === 'robots') {
                loadRobots();
            } else if (targetTab === 'analytics') {
                loadAnalytics();
            } else if (targetTab === 'activity') {
                loadActivityLogs();
            } else if (targetTab === 'alerts') {
                loadAllAlerts();
            } else if (targetTab === '2fa-management') {
                load2FAUsers();
            } else if (targetTab === 'security-threats') {
                loadSecurityThreats();
            } else if (targetTab === 'admin-2fa') {
                loadAdmin2FAStatus();
            }
            
            // Always update stats when switching tabs
            updateStats();
        });
    });
}

// Load all data
function loadAllData() {
    loadBookings();
    loadUsers();
    loadRobotCount();
    loadMonitoring();
    updateStats();
}

// Load total robot count
function loadRobotCount() {
    fetch('/admin/robot-count', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                totalRobotCount = data.count || 0;
                updateStats();
            } else {
                console.warn('Robot count API returned non-success status:', data);
                // Fallback to 50 if API fails
                totalRobotCount = 50;
                updateStats();
            }
        })
        .catch(error => {
            console.error('Error loading robot count:', error);
            // Fallback to 50 if API fails
            totalRobotCount = 50;
            updateStats();
        });
}

// Load bookings
function loadBookings() {
    fetch('/admin/bookings', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Bookings response:', data);
            if (data.status === 'success') {
                allBookings = data.data || [];
                displayBookings(allBookings);
                updateStats();
            } else {
                console.warn('Bookings API returned non-success status:', data);
                document.getElementById('bookings-table-body').innerHTML = 
                    '<tr><td colspan="5" class="loading">No bookings found</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading bookings:', error);
            document.getElementById('bookings-table-body').innerHTML = 
                `<tr><td colspan="5" class="loading">Error loading bookings: ${error.message || 'Unknown error'}</td></tr>`;
        });
}

// Display bookings in table
function displayBookings(bookings) {
    const tbody = document.getElementById('bookings-table-body');
    
    if (bookings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No active bookings</td></tr>';
        return;
    }
    
    tbody.innerHTML = bookings.map(booking => {
        const formattedDate = formatEasternTime(booking.booked_at);
        
        return `
            <tr>
                <td><strong>${escapeHtml(booking.username || '')}</strong></td>
                <td>${escapeHtml(booking.email || '')}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <img src="${escapeHtml(booking.robot_image || '')}" 
                             alt="${escapeHtml(booking.robot_name || '')}" 
                             style="width: 40px; height: 40px; border-radius: 8px; object-fit: cover;">
                        <span>${escapeHtml(booking.robot_name || '')}</span>
                    </div>
                </td>
                <td>${escapeHtml(formattedDate)}</td>
                <td>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="action-btn send-alert-btn" 
                                onclick="sendQuickAlert(${parseInt(booking.user_id) || 0})">
                            <i class="bx bx-bell"></i> Alert
                        </button>
                        <button class="action-btn free-robot-btn" 
                                onclick="freeRobotBooking(${parseInt(booking.user_id) || 0}, ${parseInt(booking.robot_id) || 0}, '${escapeHtml(booking.robot_name || '')}', '${escapeHtml(booking.username || '')}')"
                                title="Free this robot (user account will remain)">
                            <i class="bx bx-undo"></i> Free Robot
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Load users
function loadUsers() {
    fetch('/admin/users', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Users response:', data);
            if (data.status === 'success') {
                allUsers = data.data || [];
                displayUsers(allUsers);
                populateUserSelect(allUsers);
                updateStats();
            } else {
                console.warn('Users API returned non-success status:', data);
                document.getElementById('users-table-body').innerHTML = 
                    '<tr><td colspan="8" class="loading">No users found</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading users:', error);
                document.getElementById('users-table-body').innerHTML = 
                    `<tr><td colspan="8" class="loading">Error loading users: ${error.message || 'Unknown error'}</td></tr>`;
        });
}

// Display users in table
function displayUsers(users) {
    const tbody = document.getElementById('users-table-body');
    
    // Filter out admin users only (keep regular users and Blue Team members)
    // Blue Team members should be visible so admin can revoke their access
    const displayUsers = users.filter(user => {
        const userRole = (user.role || 'user').toLowerCase();
        return userRole !== 'admin';
    });
    
    if (displayUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = displayUsers.map(user => {
        const date = formatEasternDate(user.created_at);
        const userRole = (user.role || 'user').toLowerCase();
        let roleClass = 'user';
        let roleText = 'USER';
        
        if (userRole === 'blue_team' || userRole === 'blueteam') {
            roleClass = 'blue-team';
            roleText = 'BLUE TEAM';
        } else if (userRole === 'admin') {
            roleClass = 'admin';
            roleText = 'ADMIN';
        }
        
        const lastLogin = user.last_login ? formatEasternTime(user.last_login) : (user.created_at ? formatEasternTime(user.created_at) : 'Never');
        const isBlueTeam = userRole === 'blue_team' || userRole === 'blueteam';
        
        return `
            <tr>
                <td><input type="checkbox" class="user-checkbox" value="${user.id}" onchange="updateBulkActionButtons()" /></td>
                <td><strong>${escapeHtml(user.username || '')}</strong></td>
                <td>${escapeHtml(user.email || '')}</td>
                <td><span class="role-badge ${roleClass}">${roleText}</span></td>
                <td>${parseInt(user.booking_count) || 0}</td>
                <td>${escapeHtml(lastLogin)}</td>
                <td>${escapeHtml(date)}</td>
                <td>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="action-btn send-alert-btn" 
                                onclick="sendQuickAlert(${parseInt(user.id) || 0})">
                            <i class="bx bx-bell"></i> Alert
                        </button>
                        ${!isBlueTeam ? `
                        <button class="action-btn blue-team-btn" 
                                onclick="grantBlueTeamAccess(${parseInt(user.id) || 0}, '${escapeHtml(user.username || '')}')"
                                title="Grant Blue Team access for security monitoring"
                                style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white;">
                            <i class="bx bx-shield-alt-2"></i> Grant Blue Team
                        </button>
                        ` : `
                        <button class="action-btn revoke-blue-team-btn" 
                                onclick="revokeBlueTeamAccess(${parseInt(user.id) || 0}, '${escapeHtml(user.username || '')}')"
                                title="Revoke Blue Team access - User will lose access to security dashboard"
                                style="background: linear-gradient(135deg, #f59e0b, #eab308); color: white;">
                            <i class="bx bx-shield-x"></i> Revoke Blue Team
                        </button>
                        `}
                        <button class="action-btn delete-btn" 
                                onclick="deleteUser(${parseInt(user.id) || 0}, '${escapeHtml(user.username || '')}')"
                                title="Delete user account and all bookings">
                            <i class="bx bx-trash"></i> Delete
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Populate user select for alert form
function populateUserSelect(users) {
    const select = document.getElementById('alert-user-select');
    // Filter out admin users - only show regular users for alerts
    const regularUsers = users.filter(user => user.role !== 'admin' && user.role !== 'ADMIN');
    select.innerHTML = '<option value="">-- Select a user --</option>' +
        regularUsers.map(user => 
            `<option value="${user.id}">${escapeHtml(user.username)} (${escapeHtml(user.email)})</option>`
        ).join('');
}

// Setup alert form
function setupAlertForm() {
    const form = document.getElementById('send-alert-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        fetch('/admin/send-alert', {
            method: 'POST',
            credentials: 'include',
            body: formData
        })
        .then(response => response.json())
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Alert sent successfully! The user will receive it within 3 seconds.');
                form.reset();
                loadAllAlerts(); // Reload alerts list
            } else {
                alert('Error: ' + (data.error || 'Failed to send alert'));
            }
        })
        .catch(error => {
            console.error('Error sending alert:', error);
            alert('Error sending alert');
        });
    });
    
    // Load alerts when alerts tab is opened
    if (document.getElementById('alerts-tab')) {
        loadAllAlerts();
    }
}

// Send quick alert
function sendQuickAlert(userId) {
    const message = "Thanks for having the robopet, do give a feedback!";
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('message', message);
    
    fetch('/admin/send-alert', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Alert sent successfully! The user will receive it within 3 seconds.');
            console.log('Quick alert sent:', data);
        } else {
            alert('Error: ' + (data.error || 'Failed to send alert'));
        }
    })
    .catch(error => {
        console.error('Error sending alert:', error);
        alert('Error sending alert');
    });
}

// Load monitoring data
function loadMonitoring() {
    // Calculate bookings today
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const bookingsToday = allBookings.filter(booking => {
        const bookingDate = new Date(booking.booked_at);
        bookingDate.setHours(0, 0, 0, 0);
        return bookingDate.getTime() === today.getTime();
    }).length;
    
    document.getElementById('bookings-today').textContent = bookingsToday;
    
    // Calculate new users today
    const usersToday = allUsers.filter(user => {
        if (!user.created_at) return false;
        const userDate = new Date(user.created_at);
        userDate.setHours(0, 0, 0, 0);
        return userDate.getTime() === today.getTime();
    }).length;
    
    document.getElementById('users-today').textContent = usersToday;
    
    // Calculate average booking duration (simplified)
    const avgDuration = allBookings.length > 0 ? 
        Math.round(allBookings.length * 2.5) : 0;
    document.getElementById('avg-duration').textContent = avgDuration + 'h';
    
    // Find most popular robot
    const robotCounts = {};
    allBookings.forEach(booking => {
        const robotName = booking.robot_name;
        robotCounts[robotName] = (robotCounts[robotName] || 0) + 1;
    });
    
    const popularRobot = Object.keys(robotCounts).length > 0 ?
        Object.keys(robotCounts).reduce((a, b) => robotCounts[a] > robotCounts[b] ? a : b) : '-';
    document.getElementById('popular-robot').textContent = popularRobot;
}

// Update stats cards
function updateStats() {
    // Count only regular users (not admins)
    const regularUsers = allUsers.filter(user => user.role !== 'admin' && user.role !== 'ADMIN');
    document.getElementById('total-users').textContent = regularUsers.length;
    
    // Calculate total active bookings (total number of robot bookings, not number of users)
    const totalActiveBookings = allBookings.length;
    document.getElementById('total-bookings').textContent = totalActiveBookings;
    
    // Verify consistency: sum of all user booking counts should equal total active bookings
    const sumOfUserBookingCounts = regularUsers.reduce((sum, user) => sum + (parseInt(user.booking_count) || 0), 0);
    if (sumOfUserBookingCounts !== totalActiveBookings) {
        console.warn(`Booking count mismatch: Total active bookings (${totalActiveBookings}) does not match sum of user booking counts (${sumOfUserBookingCounts})`);
        // Use the total from bookings as the source of truth
    }
    
    // Calculate total robots: total robots (50) - booked robots = available robots
    // But since the stat is labeled "Total Robots", show the total count
    // If totalRobotCount is 0, use 50 as fallback
    const totalRobots = totalRobotCount > 0 ? totalRobotCount : 50;
    const bookedRobots = allBookings.length;
    const availableRobots = totalRobots - bookedRobots;
    
    // Show total robots (50) - booked robots = available robots
    // Actually, based on user request: show "50 - robot booked" which is available robots
    document.getElementById('total-robots').textContent = availableRobots;
    
    document.getElementById('pending-alerts').textContent = '0'; // Placeholder
}

// Delete user account and all bookings
// Show create admin modal
function showCreateAdminModal() {
    const section = document.getElementById('create-admin-section');
    if (section) {
        section.style.display = 'block';
        // Scroll to form
        section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        // Focus on username field
        document.getElementById('admin-username')?.focus();
    }
}

// Hide create admin modal
function hideCreateAdminModal() {
    const section = document.getElementById('create-admin-section');
    if (section) {
        section.style.display = 'none';
        // Reset form
        const form = document.getElementById('create-admin-form');
        if (form) {
            form.reset();
        }
    }
}

// Create admin user
function createAdminUser(event) {
    event.preventDefault();
    
    const username = document.getElementById('admin-username')?.value.trim();
    const email = document.getElementById('admin-email')?.value.trim();
    const password = document.getElementById('admin-password')?.value;
    
    if (!username || !email || !password) {
        alert('Please fill in all fields');
        return;
    }
    
    // Validate password length
    if (password.length < 8) {
        alert('Password must be at least 8 characters long');
        return;
    }
    
    const formData = new FormData();
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password', password);
    
    // Disable submit button
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn?.textContent;
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Creating...';
    }
    
    fetch('/admin/users/create-admin', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Admin user "${username}" created successfully!`);
            hideCreateAdminModal();
            loadUsers(); // Refresh user list
        } else {
            alert(data.error || 'Failed to create admin user');
        }
    })
    .catch(error => {
        console.error('Error creating admin user:', error);
        alert('An error occurred while creating the admin user. Please try again.');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText || '<i class="bx bx-user-plus"></i> Create Admin';
        }
    });
}

// Grant Blue Team access to a user
function grantBlueTeamAccess(userId, username) {
    if (!confirm(`Are you sure you want to grant Blue Team access to "${username}"?\n\nBlue Team members can:\n- View security analytics\n- Monitor security events\n- Access activity logs\n- Chat with admin`)) {
        return;
    }
    
    fetch(`/admin/users/${userId}/role`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            role: 'blue_team'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Blue Team access granted to "${username}" successfully!`);
            loadUsers(); // Refresh the users list
        } else {
            alert('Error: ' + (data.error || 'Failed to grant Blue Team access'));
        }
    })
    .catch(error => {
        console.error('Error granting Blue Team access:', error);
        alert('Error granting Blue Team access');
    });
}

// Revoke Blue Team access from a user
function revokeBlueTeamAccess(userId, username) {
    if (!confirm(`Are you sure you want to revoke Blue Team access from "${username}"?\n\nThis will:\n- Remove their access to the Blue Team security dashboard\n- Change their role back to regular user\n- They will need to be granted access again to regain Blue Team privileges`)) {
        return;
    }
    
    fetch(`/admin/users/${userId}/role`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            role: 'user'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Blue Team access revoked from "${username}" successfully!`);
            loadUsers(); // Refresh the users list
        } else {
            alert('Error: ' + (data.error || 'Failed to revoke Blue Team access'));
        }
    })
    .catch(error => {
        console.error('Error revoking Blue Team access:', error);
        alert('Error revoking Blue Team access');
    });
}

function deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user "${username}"?\n\nThis will:\n- Delete the user account\n- Free all robots booked by this user\n- Delete all alerts for this user\n\nThis action cannot be undone!`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('user_id', userId);
    
    fetch('/admin/delete-user', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`User "${username}" deleted successfully!\n${data.message || ''}`);
            // Reload users and bookings
            loadUsers();
            loadBookings();
            updateStats();
        } else {
            alert('Error: ' + (data.error || 'Failed to delete user'));
        }
    })
    .catch(error => {
        console.error('Error deleting user:', error);
        alert('Error deleting user. Please try again.');
    });
}

// Free a robot booking (returns the robot without deleting the user)
function freeRobotBooking(userId, robotId, robotName, username) {
    if (!confirm(`Are you sure you want to free the robot "${robotName}" from user "${username}"?\n\nThis will:\n- Return the robot (make it available for others)\n- Keep the user account intact\n- User will no longer have this robot`)) {
        return;
    }
    
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('robot_id', robotId);
    
    fetch('/admin/free-robot', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Robot "${robotName}" freed successfully!\nThe robot is now available for other users.`);
            // Reload bookings to reflect the change
            loadBookings();
            updateStats();
        } else {
            alert('Error: ' + (data.error || 'Failed to free robot'));
        }
    })
    .catch(error => {
        console.error('Error freeing robot:', error);
        alert('Error freeing robot. Please try again.');
    });
}

// Format date and time to Eastern Time (EST/EDT - GMT-5/GMT-4)
// Uses America/New_York timezone which automatically handles EST (winter) and EDT (summer)
// Format matches Windows taskbar: "H:MM AM/PM MM/DD/YYYY" (time first, then date)
function formatEasternTime(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        // Parse the date string - if it's from database (UTC), it should be in ISO format
        const date = new Date(dateString);
        
        // Verify the date is valid
        if (isNaN(date.getTime())) {
            return dateString;
        }
        
        // Subtract 5 hours (user requested -5hrs)
        date.setHours(date.getHours() - 5);
        
        // Format time - Windows taskbar format
        const timeFormatter = new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
        
        // Format date
        const dateFormatter = new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
        
        const time = timeFormatter.format(date);
        const dateParts = dateFormatter.formatToParts(date);
        const month = dateParts.find(p => p.type === 'month')?.value.padStart(2, '0');
        const day = dateParts.find(p => p.type === 'day')?.value.padStart(2, '0');
        const year = dateParts.find(p => p.type === 'year')?.value;
        
        // Windows taskbar format: "H:MM AM/PM MM/DD/YYYY"
        return `${time} ${month}/${day}/${year}`;
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateString;
    }
}

// Format date - date only, no time (with -5 hours offset)
function formatEasternDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        
        if (isNaN(date.getTime())) {
            return dateString;
        }
        
        // Subtract 5 hours (user requested -5hrs)
        date.setHours(date.getHours() - 5);
        
        // Format date
        const formatter = new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
        
        const parts = formatter.formatToParts(date);
        const month = parts.find(p => p.type === 'month')?.value.padStart(2, '0');
        const day = parts.find(p => p.type === 'day')?.value.padStart(2, '0');
        const year = parts.find(p => p.type === 'year')?.value;
        
        return `${month}/${day}/${year}`;
    } catch (e) {
        console.error('Error formatting date:', e);
        return dateString;
    }
}

// Chat Support Functions
let currentChatUserId = null;
let chatPollInterval = null;

function loadChatConversations() {
    fetch('/admin/chat/conversations', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            displayChatConversations(data.data || []);
            if (currentChatUserId) {
                loadChatMessagesForUser(currentChatUserId);
            }
        } else {
            document.getElementById('chat-conversations-list').innerHTML = 
                '<div class="loading">No conversations found</div>';
        }
    })
    .catch(error => {
        console.error('Error loading chat conversations:', error);
        document.getElementById('chat-conversations-list').innerHTML = 
            '<div class="loading">Error loading conversations</div>';
    });
}

function displayChatConversations(conversations) {
    const listContainer = document.getElementById('chat-conversations-list');
    if (!listContainer) return;
    
    if (conversations.length === 0) {
        listContainer.innerHTML = '<div class="loading">No conversations yet</div>';
        return;
    }
    
    listContainer.innerHTML = conversations.map(conv => {
        const date = conv.latest_message_time ? formatEasternTime(conv.latest_message_time) : 'No messages';
        const unreadBadge = conv.unread_count > 0 ? 
            `<span class="conversation-badge">${conv.unread_count}</span>` : '';
        const activeClass = currentChatUserId === conv.user_id ? 'active' : '';
        const safeUsername = escapeHtml(conv.username);
        const safeEmail = escapeHtml(conv.email);
        
        return `
            <div class="conversation-item ${activeClass}" data-user-id="${conv.user_id}" onclick="selectChatConversation(${conv.user_id}, '${safeUsername}', '${safeEmail}')">
                <div class="conversation-item-header">
                    <span class="conversation-username">${safeUsername}</span>
                    ${unreadBadge}
                </div>
                <div class="conversation-preview">${escapeHtml(conv.latest_message || 'No messages')}</div>
                <div class="conversation-time">${escapeHtml(date)}</div>
            </div>
        `;
    }).join('');
}

function selectChatConversation(userId, username, email) {
    currentChatUserId = userId;
    
    // Update active state
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
        if (parseInt(item.getAttribute('data-user-id')) === userId) {
            item.classList.add('active');
        }
    });
    
    // Show messages panel
    document.getElementById('chat-messages-panel-empty').style.display = 'none';
    document.getElementById('chat-messages-panel').style.display = 'flex';
    
    // Update header
    document.getElementById('chat-user-name').textContent = username;
    document.getElementById('chat-user-email').textContent = email;
    
    // Load messages
    loadChatMessagesForUser(userId);
    
    // Start polling for this conversation
    startAdminChatPolling();
}

function loadChatMessagesForUser(userId) {
    fetch(`/admin/chat/messages?user_id=${userId}`, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            displayAdminChatMessages(data.data || []);
        }
    })
    .catch(error => {
        console.error('Error loading chat messages:', error);
    });
}

function displayAdminChatMessages(messages) {
    const messagesContainer = document.getElementById('admin-chat-messages');
    if (!messagesContainer) return;
    
    if (messages.length === 0) {
        messagesContainer.innerHTML = '<div class="chat-empty">No messages yet. Start the conversation!</div>';
        return;
    }
    
    messagesContainer.innerHTML = messages.map(msg => {
        const date = new Date(msg.created_at);
        const time = formatChatTime(date);
        const isAdmin = msg.is_from_admin;
        
        return `
            <div class="admin-chat-message ${isAdmin ? 'admin' : 'user'}">
                <div class="admin-message-bubble">${escapeHtml(msg.message)}</div>
                <div class="admin-message-time">${time}</div>
            </div>
        `;
    }).join('');
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatChatTime(date) {
    // Convert to Eastern Time (EST/EDT - GMT-5/GMT-4)
    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York', // Automatically uses EST (GMT-5) or EDT (GMT-4) based on DST
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
    
    return formatter.format(date);
}

// Validate chat message on client side (admin)
function validateAdminChatMessage(message) {
    if (!message || !message.trim()) {
        return { valid: false, error: "Message cannot be empty" };
    }
    
    const trimmed = message.trim();
    
    // Check length
    if (trimmed.length < 1) {
        return { valid: false, error: "Message cannot be empty" };
    }
    if (trimmed.length > 1000) {
        return { valid: false, error: "Message is too long (max 1000 characters)" };
    }
    
    // Check for dangerous patterns
    const dangerousPatterns = [
        /<script/i,
        /<\/script>/i,
        /javascript:/i,
        /onerror\s*=/i,
        /onclick\s*=/i,
        /onload\s*=/i,
        /<iframe/i,
        /<object/i,
        /<embed/i,
        /expression\s*\(/i,
        /vbscript:/i,
    ];
    
    for (const pattern of dangerousPatterns) {
        if (pattern.test(trimmed)) {
            return { valid: false, error: "Message contains invalid content. Please remove any scripts." };
        }
    }
    
    return { valid: true, error: "" };
}

function sendAdminChatMessage() {
    if (!currentChatUserId) {
        alert('Please select a conversation first');
        return;
    }
    
    const input = document.getElementById('admin-chat-input');
    const sendBtn = document.getElementById('admin-chat-send-btn');
    
    if (!input || !sendBtn) return;
    
    const message = input.value;
    
    // Validate message
    const validation = validateAdminChatMessage(message);
    if (!validation.valid) {
        alert(validation.error);
        return;
    }
    
    // Disable input while sending
    input.disabled = true;
    sendBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('user_id', currentChatUserId);
    formData.append('message', message.trim());
    
    fetch('/admin/chat/send', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.value = '';
            // Reload messages
            loadChatMessagesForUser(currentChatUserId);
            // Reload conversations to update unread counts
            loadChatConversations();
        } else {
            alert('Error: ' + (data.error || 'Failed to send message'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Error sending message. Please try again.');
    })
    .finally(() => {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    });
}

function startAdminChatPolling() {
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
    }
    
    chatPollInterval = setInterval(() => {
        if (currentChatUserId) {
            loadChatMessagesForUser(currentChatUserId);
            loadChatConversations();
        }
    }, 3000); // Poll every 3 seconds
}

// Setup admin chat input
document.addEventListener('DOMContentLoaded', function() {
    const adminChatInput = document.getElementById('admin-chat-input');
    const adminChatSendBtn = document.getElementById('admin-chat-send-btn');
    
    if (adminChatInput && adminChatSendBtn) {
        adminChatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAdminChatMessage();
            }
        });
        
        adminChatSendBtn.addEventListener('click', function() {
            sendAdminChatMessage();
        });
    }
});

// Utility function to escape HTML
function escapeHtml(text) {
    if (text == null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ==================== ANNOUNCEMENTS MANAGEMENT ====================

let allAnnouncements = [];

function loadAnnouncementsAdmin() {
    fetch('/admin/announcements?active_only=false', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            allAnnouncements = data.data || [];
            displayAnnouncementsAdmin();
        } else {
            console.error('Failed to load announcements:', data);
            document.getElementById('announcements-list-admin').innerHTML = 
                '<div class="error">Failed to load announcements</div>';
        }
    })
    .catch(error => {
        console.error('Error loading announcements:', error);
        document.getElementById('announcements-list-admin').innerHTML = 
            '<div class="error">Error loading announcements</div>';
    });
}

function displayAnnouncementsAdmin() {
    const container = document.getElementById('announcements-list-admin');
    if (!container) return;
    
    if (allAnnouncements.length === 0) {
        container.innerHTML = '<div class="empty-state">No announcements yet. Create one above!</div>';
        return;
    }
    
    // Sort by created_at (newest first)
    const sorted = [...allAnnouncements].sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
    });
    
    container.innerHTML = sorted.map(ann => {
        const createdDate = formatEasternTime(ann.created_at);
        const updatedDate = ann.updated_at ? formatEasternTime(ann.updated_at) : 'Never';
        const statusClass = ann.is_active ? 'active' : 'inactive';
        const statusText = ann.is_active ? 'Active' : 'Inactive';
        
        return `
            <div class="announcement-admin-item ${statusClass}">
                <div class="announcement-admin-header">
                    <h4>${escapeHtml(ann.title)}</h4>
                    <span class="announcement-status ${statusClass}">${statusText}</span>
                </div>
                <div class="announcement-admin-message">${escapeHtml(ann.message)}</div>
                <div class="announcement-admin-meta">
                    <span>Created: ${createdDate}</span>
                    <span>Updated: ${updatedDate}</span>
                </div>
                <div class="announcement-admin-actions">
                    ${ann.is_active ? 
                        `<button class="btn-secondary" onclick="toggleAnnouncement(${ann.id}, false)">Deactivate</button>` :
                        `<button class="btn-secondary" onclick="toggleAnnouncement(${ann.id}, true)">Activate</button>`
                    }
                    <button class="btn-edit" onclick="editAnnouncement(${ann.id})">Edit</button>
                    <button class="btn-danger" onclick="deleteAnnouncement(${ann.id})">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

function createAnnouncement(event) {
    event.preventDefault();
    
    const titleInput = document.getElementById('announcement-title');
    const messageInput = document.getElementById('announcement-message');
    
    const title = titleInput.value.trim();
    const message = messageInput.value.trim();
    
    if (!title || !message) {
        alert('Please fill in both title and message');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('message', message);
    
    fetch('/admin/announcements', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to create announcement');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert('Announcement created successfully!');
            titleInput.value = '';
            messageInput.value = '';
            loadAnnouncementsAdmin();
        } else {
            throw new Error(data.message || 'Failed to create announcement');
        }
    })
    .catch(error => {
        console.error('Error creating announcement:', error);
        alert('Error: ' + error.message);
    });
}

function toggleAnnouncement(id, isActive) {
    const formData = new FormData();
    formData.append('is_active', isActive);
    
    fetch(`/admin/announcements/${id}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to update announcement');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            loadAnnouncementsAdmin();
        } else {
            throw new Error(data.message || 'Failed to update announcement');
        }
    })
    .catch(error => {
        console.error('Error updating announcement:', error);
        alert('Error: ' + error.message);
    });
}

function editAnnouncement(id) {
    const ann = allAnnouncements.find(a => a.id === id);
    if (!ann) {
        alert('Announcement not found');
        return;
    }
    
    const newTitle = prompt('Enter new title:', ann.title);
    if (newTitle === null) return;
    
    const newMessage = prompt('Enter new message:', ann.message);
    if (newMessage === null) return;
    
    const formData = new FormData();
    formData.append('title', newTitle.trim());
    formData.append('message', newMessage.trim());
    
    fetch(`/admin/announcements/${id}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to update announcement');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert('Announcement updated successfully!');
            loadAnnouncementsAdmin();
        } else {
            throw new Error(data.message || 'Failed to update announcement');
        }
    })
    .catch(error => {
        console.error('Error updating announcement:', error);
        alert('Error: ' + error.message);
    });
}

function deleteAnnouncement(id) {
    if (!confirm('Are you sure you want to delete this announcement? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/admin/announcements/${id}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || 'Failed to delete announcement');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            alert('Announcement deleted successfully!');
            loadAnnouncementsAdmin();
        } else {
            throw new Error(data.message || 'Failed to delete announcement');
        }
    })
    .catch(error => {
        console.error('Error deleting announcement:', error);
        alert('Error: ' + error.message);
    });
}

// ==================== ROBOT MANAGEMENT ====================

let allRobots = [];

function loadRobots() {
    fetch('/admin/robots', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            allRobots = data.data || [];
            displayRobots(allRobots);
        }
    })
    .catch(error => {
        console.error('Error loading robots:', error);
    });
}

function displayRobots(robots) {
    const tbody = document.getElementById('robots-table-body');
    if (!tbody) return;
    
    if (robots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No robots found</td></tr>';
        return;
    }
    
    tbody.innerHTML = robots.map(robot => {
        const statusClass = robot.status === 'available' ? 'available' : 
                           robot.status === 'maintenance' ? 'maintenance' : 'unavailable';
        return `
            <tr>
                <td>${robot.id}</td>
                <td><strong>${escapeHtml(robot.name || '')}</strong></td>
                <td><span class="status-badge ${statusClass}">${escapeHtml(robot.status || 'available')}</span></td>
                <td>${escapeHtml(robot.category || '-')}</td>
                <td>
                    <button class="action-btn" onclick="editRobot(${robot.id})" style="background: var(--primary-blue);">
                        <i class="bx bx-edit"></i> Edit
                    </button>
                    <button class="action-btn delete-btn" onclick="deleteRobot(${robot.id}, '${escapeHtml(robot.name || '')}')">
                        <i class="bx bx-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function createRobot(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    fetch('/admin/robots', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Robot created successfully!');
            event.target.reset();
            loadRobots();
        } else {
            alert('Error: ' + (data.error || 'Failed to create robot'));
        }
    })
    .catch(error => {
        console.error('Error creating robot:', error);
        alert('Error creating robot');
    });
}

function editRobot(robotId) {
    const robot = allRobots.find(r => r.id === robotId);
    if (!robot) return;
    
    const name = prompt('Enter new name:', robot.name);
    if (name === null) return;
    
    const photoUrl = prompt('Enter photo URL:', robot.photo_url);
    if (photoUrl === null) return;
    
    const description = prompt('Enter description:', robot.description || '');
    const category = prompt('Enter category:', robot.category || '');
    const status = prompt('Enter status (available/maintenance/unavailable):', robot.status || 'available');
    
    const formData = new FormData();
    formData.append('name', name.trim());
    formData.append('photo_url', photoUrl.trim());
    if (description) formData.append('description', description.trim());
    if (category) formData.append('category', category.trim());
    if (status) formData.append('status', status.trim());
    
    fetch(`/admin/robots/${robotId}`, {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Robot updated successfully!');
            loadRobots();
        } else {
            alert('Error: ' + (data.error || 'Failed to update robot'));
        }
    })
    .catch(error => {
        console.error('Error updating robot:', error);
        alert('Error updating robot');
    });
}

function deleteRobot(robotId, robotName) {
    if (!confirm(`Are you sure you want to delete robot "${robotName}"?`)) {
        return;
    }
    
    fetch(`/admin/robots/${robotId}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Robot deleted successfully!');
            loadRobots();
        } else {
            alert('Error: ' + (data.error || 'Failed to delete robot'));
        }
    })
    .catch(error => {
        console.error('Error deleting robot:', error);
        alert('Error deleting robot');
    });
}

// ==================== ANALYTICS ====================

function loadAnalytics() {
    const startDate = document.getElementById('analytics-start-date')?.value || '';
    const endDate = document.getElementById('analytics-end-date')?.value || '';
    
    let url = '/admin/analytics?';
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    
    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayAnalytics(data.data);
        }
    })
    .catch(error => {
        console.error('Error loading analytics:', error);
    });
}

function displayAnalytics(analytics) {
    document.getElementById('analytics-total-bookings').textContent = analytics.total_bookings || 0;
    
    // Popular robots - make clickable to show robot-specific graph
    const popularList = document.getElementById('popular-robots-list');
    if (popularList && analytics.popular_robots) {
        popularList.innerHTML = analytics.popular_robots.map((r, idx) => 
            `<div style="padding: 5px 0; cursor: pointer; color: #6C5CE7; text-decoration: underline;" 
                  onclick="showRobotBookingGraph(${r.robot_id}, '${escapeHtml(r.robot_name)}')" 
                  title="Click to see booking graph for this robot">
                ${idx + 1}. ${escapeHtml(r.robot_name)} (${r.booking_count} bookings)
            </div>`
        ).join('') || '<div>No data</div>';
    }
    
    // Bookings trend chart
    if (analytics.bookings_by_day && typeof Chart !== 'undefined') {
        const ctx = document.getElementById('bookingsChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: analytics.bookings_by_day.map(d => {
                        const date = new Date(d.date);
                        return date.toLocaleDateString('en-US', { 
                            timeZone: 'America/New_York',
                            month: 'short', 
                            day: 'numeric' 
                        });
                    }),
                    datasets: [{
                        label: 'Bookings',
                        data: analytics.bookings_by_day.map(d => d.count),
                        borderColor: '#6C5CE7',
                        backgroundColor: 'rgba(108, 92, 231, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    }
}

function exportBookings() {
    const startDate = document.getElementById('analytics-start-date')?.value || '';
    const endDate = document.getElementById('analytics-end-date')?.value || '';
    
    let url = '/admin/export/bookings?';
    if (startDate) url += `start_date=${encodeURIComponent(startDate)}&`;
    if (endDate) url += `end_date=${encodeURIComponent(endDate)}&`;
    
    // Use fetch with credentials to ensure authentication cookie is sent
    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Accept': 'text/csv'
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Authentication required. Please log in again.');
            } else if (response.status === 403) {
                throw new Error('You do not have permission to export bookings.');
            }
            throw new Error(`Export failed: ${response.status} ${response.statusText}`);
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `bookings_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);
        
        // Show success notification
        if (typeof showNotification === 'function') {
            showNotification('Bookings exported successfully!', 'success');
        }
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('Failed to export bookings: ' + error.message);
    });
}

// Show robot-specific booking graph
function showRobotBookingGraph(robotId, robotName) {
    const startDate = document.getElementById('analytics-start-date')?.value || '';
    const endDate = document.getElementById('analytics-end-date')?.value || '';
    
    let url = `/admin/analytics/robot/${robotId}?`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    
    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.data && data.data.booking_days) {
            displayRobotBookingGraph(robotId, robotName, data.data.booking_days);
        } else {
            alert('No booking data found for this robot');
        }
    })
    .catch(error => {
        console.error('Error loading robot analytics:', error);
        alert('Failed to load robot booking data');
    });
}

// Display robot-specific booking graph
function displayRobotBookingGraph(robotId, robotName, bookingDays) {
    // Create or update modal for robot graph
    let modal = document.getElementById('robot-booking-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'robot-booking-modal';
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h2>Booking History: ${escapeHtml(robotName)}</h2>
                    <button onclick="closeRobotBookingModal()" style="background: none; border: none; font-size: 32px; cursor: pointer; color: var(--text-secondary); line-height: 1;">&times;</button>
                </div>
                <div class="modal-body">
                    <canvas id="robotBookingChart" style="max-height: 400px;"></canvas>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } else {
        modal.querySelector('h2').textContent = `Booking History: ${escapeHtml(robotName)}`;
    }
    
    modal.style.display = 'flex';
    
    // Prepare data for chart - create a daily count
    const dayMap = {};
    bookingDays.forEach(day => {
        dayMap[day.date] = day.count;
    });
    
    // Get date range (last 30 days if not specified)
    const today = new Date();
    const dates = [];
    const counts = [];
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split('T')[0];
        dates.push(dateStr);
        counts.push(dayMap[dateStr] || 0);
    }
    
    // Destroy existing chart if any
    const ctx = document.getElementById('robotBookingChart');
    if (window.robotBookingChartInstance) {
        window.robotBookingChartInstance.destroy();
    }
    
    // Create new chart
    if (typeof Chart !== 'undefined') {
        window.robotBookingChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates.map(d => {
                    const date = new Date(d);
                    return date.toLocaleDateString('en-US', { 
                        timeZone: 'America/New_York',
                        month: 'short', 
                        day: 'numeric' 
                    });
                }),
                datasets: [{
                    label: `Days ${escapeHtml(robotName)} was booked`,
                    data: counts,
                    backgroundColor: 'rgba(108, 92, 231, 0.6)',
                    borderColor: '#6C5CE7',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Booked ${context.parsed.y} time${context.parsed.y !== 1 ? 's' : ''}`;
                            }
                        }
                    }
                }
            }
        });
    }
}

function closeRobotBookingModal() {
    const modal = document.getElementById('robot-booking-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('robot-booking-modal');
    if (modal && event.target === modal) {
        closeRobotBookingModal();
    }
});

// ==================== ACTIVITY LOGS ====================

function loadActivityLogs() {
    const activityType = document.getElementById('activity-type-filter')?.value || '';
    let url = '/admin/activity?limit=500';
    if (activityType) url += `&activity_type=${activityType}`;
    
    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayActivityLogs(data.data);
        }
    })
    .catch(error => {
        console.error('Error loading activity logs:', error);
    });
}

/**
 * Format IP address for display (normalize IPv6, format IPv4)
 * Converts IPv6 to compressed format and ensures proper formatting
 */
function formatIPAddress(ip) {
    if (!ip || ip === 'Unknown' || ip === '-') {
        return ip || '-';
    }
    
    // Check if it's IPv6 (contains colons)
    if (ip.includes(':')) {
        // IPv6 address - normalize and compress
        try {
            // Remove leading zeros from each segment and convert to lowercase
            const segments = ip.split(':');
            const normalized = segments.map(seg => {
                if (!seg) return seg; // Empty segment (for ::)
                // Remove leading zeros, but keep at least one digit
                const cleaned = seg.toLowerCase().replace(/^0+/, '') || '0';
                return cleaned;
            });
            
            // Find the longest sequence of zero segments to compress with ::
            let longestZeroStart = -1;
            let longestZeroLength = 0;
            let currentZeroStart = -1;
            let currentZeroLength = 0;
            
            for (let i = 0; i < normalized.length; i++) {
                if (normalized[i] === '0' || normalized[i] === '') {
                    if (currentZeroStart === -1) {
                        currentZeroStart = i;
                    }
                    currentZeroLength++;
                } else {
                    if (currentZeroLength > longestZeroLength) {
                        longestZeroLength = currentZeroLength;
                        longestZeroStart = currentZeroStart;
                    }
                    currentZeroStart = -1;
                    currentZeroLength = 0;
                }
            }
            
            // Check if the last segment is part of a zero group
            if (currentZeroLength > longestZeroLength) {
                longestZeroLength = currentZeroLength;
                longestZeroStart = currentZeroStart;
            }
            
            // Compress the longest zero sequence
            if (longestZeroLength > 1 && longestZeroStart !== -1) {
                const before = normalized.slice(0, longestZeroStart);
                const after = normalized.slice(longestZeroStart + longestZeroLength);
                
                // Build result
                let result = [];
                if (before.length > 0) {
                    result.push(before.join(':'));
                }
                result.push(''); // Empty string for ::
                if (after.length > 0) {
                    result.push(after.join(':'));
                }
                
                let formatted = result.join(':');
                // Handle edge cases
                if (formatted.startsWith('::')) {
                    return formatted;
                } else if (formatted.endsWith('::')) {
                    return formatted;
                } else if (formatted === ':') {
                    return '::';
                }
                return formatted;
            }
            
            // No compression needed, just return normalized
            return normalized.join(':');
        } catch (e) {
            // If parsing fails, return original (lowercased)
            return ip.toLowerCase();
        }
    } else {
        // IPv4 address - return as-is (already in correct format)
        return ip;
    }
}

function displayActivityLogs(activities) {
    const tbody = document.getElementById('activity-table-body');
    if (!tbody) return;
    
    if (activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No activity logs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = activities.map(activity => {
        const date = formatEasternTime(activity.created_at);
        const formattedIP = formatIPAddress(activity.ip_address);
        return `
            <tr>
                <td>${escapeHtml(activity.username || 'Unknown')}</td>
                <td><span class="status-badge">${escapeHtml(activity.activity_type || '')}</span></td>
                <td>${escapeHtml(activity.description || '-')}</td>
                <td>${escapeHtml(formattedIP)}</td>
                <td>${escapeHtml(date)}</td>
            </tr>
        `;
    }).join('');
}

// Setup activity filter change and search
document.addEventListener('DOMContentLoaded', function() {
    const activityFilter = document.getElementById('activity-type-filter');
    if (activityFilter) {
        activityFilter.addEventListener('change', loadActivityLogs);
    }
    
    // Setup user search input
    const userSearchInput = document.getElementById('user-search-input');
    if (userSearchInput) {
        userSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchUsers();
            }
        });
    }
});

// ==================== SEARCH & BULK OPERATIONS ====================

function searchUsers() {
    const query = document.getElementById('user-search-input')?.value || '';
    if (!query.trim()) {
        loadUsers(); // Load all if empty
        return;
    }
    
    fetch(`/admin/search/users?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            allUsers = data.data || [];
            displayUsers(allUsers);
            updateStats();
        }
    })
    .catch(error => {
        console.error('Error searching users:', error);
    });
}

function toggleSelectAllUsers(checkbox) {
    const checkboxes = document.querySelectorAll('.user-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateBulkActionButtons();
}

function updateBulkActionButtons() {
    const checked = document.querySelectorAll('.user-checkbox:checked');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    
    if (bulkDeleteBtn) bulkDeleteBtn.disabled = checked.length === 0;
}

function bulkDeleteUsers() {
    const checked = document.querySelectorAll('.user-checkbox:checked');
    const userIds = Array.from(checked).map(cb => parseInt(cb.value));
    
    if (userIds.length === 0) {
        alert('Please select users to delete');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${userIds.length} user(s)? This action cannot be undone!`)) {
        return;
    }
    
    const formData = new FormData();
    userIds.forEach(id => formData.append('user_ids', id));
    
    fetch('/admin/users/bulk-delete', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Successfully deleted ${data.deleted_count || userIds.length} user(s)`);
            loadUsers();
            loadBookings();
            updateStats();
        } else {
            alert('Error: ' + (data.error || 'Failed to delete users'));
        }
    })
    .catch(error => {
        console.error('Error bulk deleting users:', error);
        alert('Error deleting users');
    });
}

// ==================== Alert Management Functions ====================

function loadAllAlerts() {
    const tbody = document.getElementById('all-alerts-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading alerts...</td></tr>';
    
    fetch('/admin/alerts?limit=100', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.data) {
            displayAllAlerts(data.data);
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="error">Error loading alerts: ' + (data.error || 'Unknown error') + '</td></tr>';
        }
    })
    .catch(error => {
        console.error('Error loading alerts:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="error">Error loading alerts</td></tr>';
    });
}

function displayAllAlerts(alerts) {
    const tbody = document.getElementById('all-alerts-table-body');
    if (!tbody) return;
    
    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--text-secondary);">No alerts found</td></tr>';
        return;
    }
    
    tbody.innerHTML = alerts.map(alert => {
        const date = new Date(alert.created_at);
        const formattedDate = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <tr>
                <td>${alert.id}</td>
                <td>${escapeHtml(alert.username)}</td>
                <td>${escapeHtml(alert.email)}</td>
                <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(alert.message)}">
                    ${escapeHtml(alert.message)}
                </td>
                <td>
                    ${alert.read 
                        ? '<span style="color: var(--text-secondary);">Read</span>'
                        : '<span style="color: var(--success); font-weight: 600;">Unread</span>'
                    }
                </td>
                <td>${formattedDate}</td>
                <td>
                    <button 
                        class="btn-danger" 
                        onclick="deleteAlert(${alert.id})"
                        style="padding: 6px 12px; background: var(--error); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem;"
                        title="Delete this alert"
                    >
                        <i class="bx bx-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function deleteAlert(alertId) {
    if (!confirm('Are you sure you want to delete this alert?')) {
        return;
    }
    
    fetch(`/admin/alerts/${alertId}`, {
        method: 'DELETE',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadAllAlerts(); // Refresh the list
        } else {
            alert('Error: ' + (data.error || 'Failed to delete alert'));
        }
    })
    .catch(error => {
        console.error('Error deleting alert:', error);
        alert('Error deleting alert');
    });
}

function deleteOldAlerts() {
    if (!confirm('Are you sure you want to delete all alerts older than 30 days?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('days_old', '30');
    
    fetch('/admin/alerts/delete-old', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`Successfully deleted ${data.deleted_count || 0} old alerts`);
            loadAllAlerts(); // Refresh the list
        } else {
            alert('Error: ' + (data.error || 'Failed to delete old alerts'));
        }
    })
    .catch(error => {
        console.error('Error deleting old alerts:', error);
        alert('Error deleting old alerts');
    });
}

// ==================== 2FA Management Functions ====================

// Load Security Threats
function loadSecurityThreats() {
    const tbody = document.getElementById('security-threats-table-body');
    tbody.innerHTML = '<tr><td colspan="9" class="loading">Loading security threats...</td></tr>';
    
    const severityFilter = document.getElementById('threat-severity-filter')?.value || 'all';
    const statusFilter = document.getElementById('threat-status-filter')?.value || 'all';
    
    let url = '/admin/security-threats?';
    if (severityFilter !== 'all') {
        url += `severity=${severityFilter}&`;
    }
    if (statusFilter !== 'all') {
        url += `resolved=${statusFilter === 'resolved' ? 'true' : 'false'}&`;
    }
    
    fetch(url, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displaySecurityThreats(data.data);
        } else {
            tbody.innerHTML = `<tr><td colspan="9" class="error">Error: ${data.error || 'Failed to load threats'}</td></tr>`;
        }
    })
    .catch(error => {
        console.error('Error loading security threats:', error);
        tbody.innerHTML = '<tr><td colspan="9" class="error">Error loading security threats</td></tr>';
    });
}

// Display Security Threats
function displaySecurityThreats(threats) {
    const tbody = document.getElementById('security-threats-table-body');
    
    if (threats.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No security threats found</td></tr>';
        return;
    }
    
    tbody.innerHTML = threats.map(threat => {
        const date = new Date(threat.created_at).toLocaleString();
        const severityClass = threat.severity === 'critical' ? 'critical' : 'high';
        const statusBadge = threat.resolved 
            ? '<span class="status-badge resolved">Resolved</span>' 
            : '<span class="status-badge unresolved">Unresolved</span>';
        const adminResponse = threat.admin_response 
            ? `<div style="max-width: 300px; word-wrap: break-word;">${escapeHtml(threat.admin_response)}</div>` 
            : '<span style="color: #94a3b8;">No response yet</span>';
        const respondedAt = threat.admin_responded_at 
            ? new Date(threat.admin_responded_at).toLocaleString() 
            : '';
        
        return `
            <tr>
                <td>${threat.id}</td>
                <td><span class="severity-badge ${severityClass}">${threat.severity.toUpperCase()}</span></td>
                <td style="max-width: 300px; word-wrap: break-word;">${escapeHtml(threat.description)}</td>
                <td>${threat.username || 'Unknown'}</td>
                <td>${threat.ip_address || 'N/A'}</td>
                <td>${date}</td>
                <td>${statusBadge}</td>
                <td>${adminResponse}</td>
                <td>
                    ${!threat.admin_response ? `
                    <button class="action-btn" onclick="showRespondToThreatModal(${threat.id}, '${escapeHtml(threat.description.replace(/'/g, "\\'"))}')" 
                            style="background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 6px 12px; font-size: 12px;">
                        <i class="bx bx-message-dots"></i> Respond
                    </button>
                    ` : `
                    <button class="action-btn" onclick="showRespondToThreatModal(${threat.id}, '${escapeHtml(threat.description.replace(/'/g, "\\'"))}', '${escapeHtml((threat.admin_response || '').replace(/'/g, "\\'"))}')" 
                            style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 6px 12px; font-size: 12px;">
                        <i class="bx bx-edit"></i> Update Response
                    </button>
                    `}
                    ${!threat.resolved ? `
                    <button class="action-btn" onclick="resolveThreat(${threat.id})" 
                            style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 6px 12px; font-size: 12px; margin-top: 5px;">
                        <i class="bx bx-check"></i> Mark Resolved
                    </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

// Show Respond to Threat Modal
function showRespondToThreatModal(eventId, description, existingResponse = '') {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3><i class="bx bx-message-dots"></i> Respond to Security Threat</h3>
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
            </div>
            <div class="modal-body">
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: var(--text-primary); font-weight: 600;">Threat Description:</label>
                    <div style="padding: 10px; background: var(--card-bg); border-radius: 4px; border: 1px solid var(--border-color); color: var(--text-secondary);">
                        ${escapeHtml(description)}
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: var(--text-primary); font-weight: 600;">Your Response:</label>
                    <textarea id="threat-response-text" rows="6" style="width: 100%; padding: 10px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--card-bg); color: var(--text-primary); font-family: inherit; resize: vertical;">${escapeHtml(existingResponse)}</textarea>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: flex; align-items: center; gap: 8px; color: var(--text-primary); cursor: pointer;">
                        <input type="checkbox" id="mark-resolved-checkbox" style="width: 18px; height: 18px;">
                        <span>Mark as resolved after responding</span>
                    </label>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn-primary" onclick="submitThreatResponse(${eventId})">Submit Response</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Submit Threat Response
function submitThreatResponse(eventId) {
    const responseText = document.getElementById('threat-response-text').value.trim();
    const markResolved = document.getElementById('mark-resolved-checkbox').checked;
    
    if (!responseText) {
        alert('Please enter a response');
        return;
    }
    
    fetch(`/admin/security-threats/${eventId}/respond`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            response: responseText,
            mark_resolved: markResolved
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Response submitted successfully! Blue Team will be notified.');
            document.querySelector('.modal').remove();
            loadSecurityThreats();
        } else {
            alert('Error: ' + (data.error || 'Failed to submit response'));
        }
    })
    .catch(error => {
        console.error('Error submitting threat response:', error);
        alert('Error submitting response');
    });
}

// Resolve Threat
function resolveThreat(eventId) {
    if (!confirm('Mark this threat as resolved?')) {
        return;
    }
    
    fetch(`/blue-team/security-events/${eventId}/resolve`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadSecurityThreats();
        } else {
            alert('Error: ' + (data.error || 'Failed to resolve threat'));
        }
    })
    .catch(error => {
        console.error('Error resolving threat:', error);
        alert('Error resolving threat');
    });
}

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function load2FAUsers() {
    const tbody = document.getElementById('2fa-users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading 2FA users...</td></tr>';
    
    fetch('/admin/2fa/users', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' && data.data) {
            display2FAUsers(data.data);
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="error">Error loading 2FA users: ' + (data.error || 'Unknown error') + '</td></tr>';
        }
    })
    .catch(error => {
        console.error('Error loading 2FA users:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="error">Error loading 2FA users</td></tr>';
    });
}

function display2FAUsers(users) {
    const tbody = document.getElementById('2fa-users-table-body');
    if (!tbody) return;
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-secondary);">No users have 2FA enabled</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${escapeHtml(user.username)}</td>
            <td>${escapeHtml(user.email)}</td>
            <td>
                <span style="color: var(--success); font-weight: 600;">
                    <i class="bx bx-check-circle"></i> Enabled
                </span>
            </td>
            <td>
                ${user.backup_codes_count > 0 
                    ? `<span style="color: var(--text-primary);">${user.backup_codes_count} remaining</span>`
                    : '<span style="color: var(--text-secondary);">None</span>'
                }
            </td>
            <td>
                <button 
                    class="btn-danger" 
                    onclick="disableUser2FA(${user.id}, '${escapeHtml(user.username)}')"
                    style="padding: 6px 12px; background: var(--error); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.9rem;"
                    title="Disable 2FA for this user"
                >
                    <i class="bx bx-x-circle"></i> Disable 2FA
                </button>
            </td>
        </tr>
    `).join('');
}

function disableUser2FA(userId, username) {
    if (!confirm(`Are you sure you want to disable 2FA for user "${username}"?\n\nThis will remove the security layer from their account.`)) {
        return;
    }
    
    fetch(`/admin/2fa/disable/${userId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`2FA has been disabled for user "${username}"`);
            load2FAUsers(); // Refresh the list
        } else {
            alert('Error: ' + (data.error || 'Failed to disable 2FA'));
        }
    })
    .catch(error => {
        console.error('Error disabling 2FA:', error);
        alert('Error disabling 2FA');
    });
}

// ==================== Admin's Own 2FA Functions ====================

function loadAdmin2FAStatus() {
    const container = document.getElementById('admin-2fa-status-container');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Loading 2FA status...</div>';
    
    fetch('/api/2fa/status', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayAdmin2FAStatus(data.data);
        } else {
            container.innerHTML = '<div class="error">Error loading 2FA status: ' + (data.error || 'Unknown error') + '</div>';
        }
    })
    .catch(error => {
        console.error('Error loading admin 2FA status:', error);
        container.innerHTML = '<div class="error">Error loading 2FA status</div>';
    });
}

function displayAdmin2FAStatus(status) {
    const container = document.getElementById('admin-2fa-status-container');
    const enableForm = document.getElementById('admin-2fa-enable-form');
    const disableForm = document.getElementById('admin-2fa-disable-form');
    
    if (status.two_factor_enabled) {
        container.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">
                        <i class="bx bx-check-circle" style="color: var(--success);"></i> Two-Factor Authentication is Enabled
                    </h3>
                    <p style="color: var(--text-secondary); margin: 0;">Your account is protected with 2FA.</p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="showAdmin2FABackupCodes()" style="padding: 10px 20px; background: var(--primary-purple); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                        <i class="bx bx-key"></i> View Backup Codes
                    </button>
                    <button onclick="showAdmin2FADisableForm()" style="padding: 10px 20px; background: var(--error); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                        <i class="bx bx-shield-x"></i> Disable 2FA
                    </button>
                </div>
            </div>
        `;
        enableForm.style.display = 'none';
        disableForm.style.display = 'none';
    } else {
        container.innerHTML = `
            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <h3 style="color: var(--text-primary); margin: 0 0 10px 0;">
                        <i class="bx bx-shield-quarter"></i> Two-Factor Authentication is Disabled
                    </h3>
                    <p style="color: var(--text-secondary); margin: 0;">Enable 2FA to add an extra layer of security to your admin account.</p>
                </div>
                <button onclick="startAdmin2FASetup()" style="padding: 12px 24px; background: var(--primary-purple); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    <i class="bx bx-shield"></i> Enable 2FA
                </button>
            </div>
        `;
        enableForm.style.display = 'none';
        disableForm.style.display = 'none';
    }
}

function startAdmin2FASetup() {
    fetch('/api/2fa/generate', {
        method: 'POST',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // The backend returns 'qr_code' not 'qr_code_url'
            const qrCodeUrl = data.data.qr_code || data.data.qr_code_url;
            if (qrCodeUrl) {
                document.getElementById('admin-2fa-qr-code').src = qrCodeUrl;
            } else {
                console.error('QR code URL not found in response:', data);
                alert('Error: QR code not generated. Please try again.');
                return;
            }
            document.getElementById('admin-2fa-enable-form').style.display = 'block';
            document.getElementById('admin-2fa-status-container').style.display = 'none';
            
            // Store secret temporarily
            window.admin2FASecret = data.data.secret;
        } else {
            alert('Error: ' + (data.error || 'Failed to generate 2FA secret'));
        }
    })
    .catch(error => {
        console.error('Error generating 2FA secret:', error);
        alert('Error generating 2FA secret');
    });
}

// Initialize admin 2FA handlers
document.addEventListener('DOMContentLoaded', function() {
    // Enable 2FA button
    const enableBtn = document.getElementById('admin-2fa-enable-btn');
    if (enableBtn) {
        enableBtn.addEventListener('click', function() {
            const code = document.getElementById('admin-2fa-verification-code').value.trim();
            if (!code || code.length !== 6) {
                alert('Please enter a valid 6-digit code');
                return;
            }
            
            const formData = new FormData();
            formData.append('secret', window.admin2FASecret);
            formData.append('verification_code', code);
            
            fetch('/api/2fa/enable', {
                method: 'POST',
                credentials: 'include',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('2FA enabled successfully!');
                    // Show backup codes
                    showAdmin2FABackupCodes(data.data.backup_codes);
                    document.getElementById('admin-2fa-enable-form').style.display = 'none';
                    loadAdmin2FAStatus();
                } else {
                    alert('Error: ' + (data.error || 'Failed to enable 2FA. Please check your code.'));
                }
            })
            .catch(error => {
                console.error('Error enabling 2FA:', error);
                alert('Error enabling 2FA');
            });
        });
    }
    
    // Cancel enable
    const cancelEnable = document.getElementById('admin-2fa-cancel-enable');
    if (cancelEnable) {
        cancelEnable.addEventListener('click', function() {
            document.getElementById('admin-2fa-enable-form').style.display = 'none';
            document.getElementById('admin-2fa-status-container').style.display = 'block';
            loadAdmin2FAStatus();
        });
    }
    
    // Disable 2FA button
    const disableBtn = document.getElementById('admin-2fa-disable-btn');
    if (disableBtn) {
        disableBtn.addEventListener('click', function() {
            const password = document.getElementById('admin-2fa-disable-password').value.trim();
            if (!password) {
                alert('Please enter your password');
                return;
            }
            
            if (!confirm('Are you sure you want to disable 2FA? This will remove the security layer from your account.')) {
                return;
            }
            
            const formData = new FormData();
            formData.append('password', password);
            
            fetch('/api/2fa/disable', {
                method: 'POST',
                credentials: 'include',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('2FA disabled successfully');
                    document.getElementById('admin-2fa-disable-form').style.display = 'none';
                    document.getElementById('admin-2fa-disable-password').value = '';
                    loadAdmin2FAStatus();
                } else {
                    alert('Error: ' + (data.error || 'Failed to disable 2FA'));
                }
            })
            .catch(error => {
                console.error('Error disabling 2FA:', error);
                alert('Error disabling 2FA');
            });
        });
    }
    
    // Cancel disable
    const cancelDisable = document.getElementById('admin-2fa-cancel-disable');
    if (cancelDisable) {
        cancelDisable.addEventListener('click', function() {
            document.getElementById('admin-2fa-disable-form').style.display = 'none';
            document.getElementById('admin-2fa-disable-password').value = '';
        });
    }
    
    // Backup codes download
    const downloadBackupCodes = document.getElementById('admin-2fa-backup-codes-download');
    if (downloadBackupCodes) {
        downloadBackupCodes.addEventListener('click', function() {
            const codes = window.admin2FABackupCodes || [];
            const text = 'Your 2FA Backup Codes\n\n' + codes.join('\n') + '\n\nSave these codes in a safe place. Each code can only be used once.';
            const blob = new Blob([text], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '2fa-backup-codes.txt';
            a.click();
            window.URL.revokeObjectURL(url);
        });
    }
    
    // Close backup codes
    const closeBackupCodes = document.getElementById('admin-2fa-backup-codes-close');
    if (closeBackupCodes) {
        closeBackupCodes.addEventListener('click', function() {
            document.getElementById('admin-2fa-backup-codes').style.display = 'none';
            window.admin2FABackupCodes = null;
        });
    }
    
    // Auto-format verification code input
    const verificationInput = document.getElementById('admin-2fa-verification-code');
    if (verificationInput) {
        verificationInput.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 6);
        });
    }
});

function showAdmin2FADisableForm() {
    document.getElementById('admin-2fa-disable-form').style.display = 'block';
    document.getElementById('admin-2fa-disable-password').focus();
}

function showAdmin2FABackupCodes(codes) {
    if (!codes) {
        // Fetch backup codes
        fetch('/api/2fa/backup-codes', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.admin2FABackupCodes = data.data.backup_codes;
                displayAdmin2FABackupCodes(data.data.backup_codes);
            } else {
                alert('Error: ' + (data.error || 'Failed to load backup codes'));
            }
        })
        .catch(error => {
            console.error('Error loading backup codes:', error);
            alert('Error loading backup codes');
        });
    } else {
        window.admin2FABackupCodes = codes;
        displayAdmin2FABackupCodes(codes);
    }
}

function displayAdmin2FABackupCodes(codes) {
    const container = document.getElementById('admin-2fa-backup-codes-list');
    container.innerHTML = codes.map(code => `<div style="padding: 5px;">${code}</div>`).join('');
    document.getElementById('admin-2fa-backup-codes').style.display = 'block';
}

// ==================== Admin Password Change Functions ====================

function initAdminPasswordChangeHandlers() {
    const changePasswordBtn = document.getElementById('admin-change-password-btn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', changeAdminPassword);
    }
}

function changeAdminPassword() {
    const oldPassword = document.getElementById('admin-old-password-input')?.value.trim();
    const newPassword = document.getElementById('admin-new-password-input')?.value.trim();
    const confirmPassword = document.getElementById('admin-confirm-password-input')?.value.trim();
    const messageDiv = document.getElementById('admin-password-change-message');
    
    // Clear previous messages
    if (messageDiv) {
        messageDiv.style.display = 'none';
        messageDiv.innerHTML = '';
    }
    
    // Validation
    if (!oldPassword || !newPassword || !confirmPassword) {
        showAdminPasswordChangeMessage('Please fill in all fields', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showAdminPasswordChangeMessage('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword === oldPassword) {
        showAdminPasswordChangeMessage('New password must be different from current password', 'error');
        return;
    }
    
    // Submit password change
    const formData = new FormData();
    formData.append('old_password', oldPassword);
    formData.append('new_password', newPassword);
    
    fetch('/api/change-password', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAdminPasswordChangeMessage('Password changed successfully!', 'success');
            // Clear form
            document.getElementById('admin-old-password-input').value = '';
            document.getElementById('admin-new-password-input').value = '';
            document.getElementById('admin-confirm-password-input').value = '';
        } else {
            showAdminPasswordChangeMessage(data.error || 'Failed to change password', 'error');
        }
    })
    .catch(error => {
        console.error('Error changing password:', error);
        showAdminPasswordChangeMessage('Error changing password. Please try again.', 'error');
    });
}

function showAdminPasswordChangeMessage(message, type) {
    const messageDiv = document.getElementById('admin-password-change-message');
    if (!messageDiv) return;
    
    messageDiv.style.display = 'block';
    messageDiv.style.padding = '12px';
    messageDiv.style.borderRadius = '8px';
    messageDiv.style.marginTop = '15px';
    
    if (type === 'success') {
        messageDiv.style.background = 'rgba(16, 185, 129, 0.1)';
        messageDiv.style.border = '1px solid #10b981';
        messageDiv.style.color = '#10b981';
        messageDiv.innerHTML = `<i class="bx bx-check-circle"></i> ${message}`;
    } else {
        messageDiv.style.background = 'rgba(239, 68, 68, 0.1)';
        messageDiv.style.border = '1px solid #ef4444';
        messageDiv.style.color = '#ef4444';
        messageDiv.innerHTML = `<i class="bx bx-error-circle"></i> ${message}`;
    }
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

