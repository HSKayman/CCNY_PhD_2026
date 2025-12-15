// Blue Team Dashboard JavaScript

let analyticsData = null;
let securityEvents = [];
let activityLogs = [];
let charts = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    loadDashboard();
    
    // Auto-refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});

// Tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Stop any existing auto-refresh
            stopSecurityEventsAutoRefresh();
            
            // Remove active class from all
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked
            btn.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // Load data for the active tab
            if (targetTab === 'analytics') {
                loadAnalytics();
            } else if (targetTab === 'security-events') {
                loadSecurityEvents();
                loadAnalytics(); // Also load analytics to show updated stats
                startSecurityEventsAutoRefresh(); // Start auto-refresh
            } else if (targetTab === 'activity-logs') {
                loadActivityLogs();
            } else if (targetTab === 'robopets-analytics') {
                loadRoboPetsAnalytics();
            } else if (targetTab === 'gcp-logs') {
                loadGCPLogs();
            } else if (targetTab === 'chat') {
                loadChatMessages();
            }
        });
    });
}

// Load dashboard data
function loadDashboard() {
    loadAnalytics();
    loadSecurityEvents();
    loadActivityLogs();
}

// Load analytics
function loadAnalytics() {
    fetch('/blue-team/analytics', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            analyticsData = data.data;
            updateStats(analyticsData);
            updateCharts(analyticsData);
            updateSummary(analyticsData);
        } else {
            console.error('Error loading analytics:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading analytics:', error);
    });
}

// Update stats cards
function updateStats(data) {
    document.getElementById('critical-events').textContent = data.security_events?.critical || 0;
    document.getElementById('high-events').textContent = data.security_events?.high || 0;
    document.getElementById('unresolved-events').textContent = data.security_events?.unresolved || 0;
    document.getElementById('events-24h').textContent = data.security_events?.last_24h || 0;
    document.getElementById('active-users-24h').textContent = data.users?.active_24h || 0;
    document.getElementById('failed-logins-24h').textContent = data.failed_logins?.last_24h || 0;
}

// Update summary
function updateSummary(data) {
    document.getElementById('total-events').textContent = data.security_events?.total || 0;
    document.getElementById('total-activities').textContent = data.activity_logs?.total || 0;
    document.getElementById('total-users').textContent = data.users?.total || 0;
    document.getElementById('events-7d').textContent = data.security_events?.last_7d || 0;
}

// Update charts
function updateCharts(data) {
    // Severity Chart
    const severityCtx = document.getElementById('severityChart');
    if (severityCtx) {
        if (charts.severity) {
            charts.severity.destroy();
        }
        charts.severity = new Chart(severityCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data.security_events?.by_severity || {}),
                datasets: [{
                    data: Object.values(data.security_events?.by_severity || {}),
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: [
                        '#ef4444',
                        '#f59e0b',
                        '#3b82f6',
                        '#10b981'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });
    }
    
    // Event Type Chart
    const eventTypeCtx = document.getElementById('eventTypeChart');
    if (eventTypeCtx) {
        if (charts.eventType) {
            charts.eventType.destroy();
        }
        const eventTypes = data.security_events?.by_type || {};
        charts.eventType = new Chart(eventTypeCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(eventTypes),
                datasets: [{
                    label: 'Events',
                    data: Object.values(eventTypes),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: '#3b82f6',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
    
    // Activity Type Chart
    const activityTypeCtx = document.getElementById('activityTypeChart');
    if (activityTypeCtx) {
        if (charts.activityType) {
            charts.activityType.destroy();
        }
        const activityTypes = data.activity_logs?.by_type || {};
        const topActivities = Object.entries(activityTypes)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        charts.activityType = new Chart(activityTypeCtx, {
            type: 'pie',
            data: {
                labels: topActivities.map(a => a[0]),
                datasets: [{
                    data: topActivities.map(a => a[1]),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(96, 165, 250, 0.8)',
                        'rgba(147, 197, 253, 0.8)',
                        'rgba(191, 219, 254, 0.8)',
                        'rgba(219, 234, 254, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });
    }
}

// Load security events
function loadSecurityEvents() {
    const severity = document.getElementById('severity-filter')?.value || '';
    const resolved = document.getElementById('resolved-filter')?.value || '';
    
    let url = '/blue-team/security-events?';
    if (severity) url += `severity=${severity}&`;
    if (resolved !== '') url += `resolved=${resolved}&`;
    
    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            securityEvents = data.data || [];
            displaySecurityEvents(securityEvents);
        } else {
            console.error('Error loading security events:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading security events:', error);
    });
}

// Display security events (with admin responses)
function displaySecurityEvents(events) {
    const tbody = document.getElementById('security-events-tbody');
    
    if (events.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No security events found</td></tr>';
        return;
    }
    
    tbody.innerHTML = events.map(event => {
        // Convert to UTC-5 (EST/EDT timezone)
        const date = formatDateUTC5(event.created_at);
        const severityClass = event.severity || 'low';
        const statusClass = event.resolved ? 'resolved' : 'unresolved';
        const statusText = event.resolved ? 'Resolved' : 'Unresolved';
        
        // Show admin response if available
        const adminResponseSection = event.admin_response 
            ? `<div style="margin-top: 8px; padding: 10px; background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; border-radius: 4px;">
                <div style="font-weight: 600; color: #3b82f6; margin-bottom: 5px; font-size: 12px;">
                    <i class="bx bx-message-dots"></i> Admin Response:
                </div>
                <div style="color: var(--text-primary); font-size: 13px;">${escapeHtml(event.admin_response)}</div>
                ${event.admin_responded_at ? `<div style="font-size: 11px; color: var(--text-secondary); margin-top: 5px;">Responded: ${formatDateUTC5(event.admin_responded_at)}</div>` : ''}
            </div>`
            : '';
        
        return `
            <tr>
                <td>${event.id}</td>
                <td><strong>${escapeHtml(event.event_type || 'Unknown')}</strong></td>
                <td><span class="severity-badge ${severityClass}">${severityClass.toUpperCase()}</span></td>
                <td>
                    <div>${escapeHtml(event.description || '')}</div>
                    ${adminResponseSection}
                </td>
                <td>${escapeHtml(event.ip_address || 'N/A')}</td>
                <td>${escapeHtml(event.username || 'N/A')}</td>
                <td>${date}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    ${!event.resolved ? `
                    <button class="action-btn" onclick="resolveEvent(${event.id})" title="Mark as resolved">
                        <i class="bx bx-check"></i> Resolve
                    </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

// Resolve security event
function resolveEvent(eventId) {
    if (!confirm('Mark this security event as resolved?')) {
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
            loadSecurityEvents();
            loadAnalytics(); // Refresh stats to show updated counts
        } else {
            alert('Error: ' + (data.error || 'Failed to resolve event'));
        }
    })
    .catch(error => {
        console.error('Error resolving event:', error);
        alert('Error resolving event');
    });
}

// Auto-refresh security events and analytics when on Security Events tab
let securityEventsRefreshInterval = null;

function startSecurityEventsAutoRefresh() {
    // Clear existing interval if any
    if (securityEventsRefreshInterval) {
        clearInterval(securityEventsRefreshInterval);
    }
    
    // Check if Security Events tab is active
    const securityEventsTab = document.getElementById('security-events-tab');
    if (securityEventsTab && securityEventsTab.classList.contains('active')) {
        // Refresh every 10 seconds when tab is active to catch admin responses
        securityEventsRefreshInterval = setInterval(() => {
            loadSecurityEvents();
            loadAnalytics(); // Also refresh analytics to show updated stats
        }, 10000); // 10 seconds
    }
}

function stopSecurityEventsAutoRefresh() {
    if (securityEventsRefreshInterval) {
        clearInterval(securityEventsRefreshInterval);
        securityEventsRefreshInterval = null;
    }
}

// Load activity logs
function loadActivityLogs() {
    fetch('/blue-team/activity-logs', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            activityLogs = data.data || [];
            displayActivityLogs(activityLogs);
            populateActivityTypeFilter(activityLogs);
        } else {
            console.error('Error loading activity logs:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading activity logs:', error);
    });
}

// Display activity logs
function displayActivityLogs(logs) {
    const tbody = document.getElementById('activity-logs-tbody');
    const searchTerm = document.getElementById('activity-search')?.value.toLowerCase() || '';
    const typeFilter = document.getElementById('activity-type-filter')?.value || '';
    
    let filteredLogs = logs;
    if (searchTerm) {
        filteredLogs = filteredLogs.filter(log => 
            (log.username || '').toLowerCase().includes(searchTerm) ||
            (log.activity_type || '').toLowerCase().includes(searchTerm) ||
            (log.description || '').toLowerCase().includes(searchTerm) ||
            (log.ip_address || '').toLowerCase().includes(searchTerm)
        );
    }
    if (typeFilter) {
        filteredLogs = filteredLogs.filter(log => log.activity_type === typeFilter);
    }
    
    if (filteredLogs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No activity logs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = filteredLogs.map(log => {
        const date = formatDateUTC5(log.created_at);
        return `
            <tr>
                <td>${log.id}</td>
                <td>${escapeHtml(log.username || 'N/A')}</td>
                <td><strong>${escapeHtml(log.activity_type || 'Unknown')}</strong></td>
                <td>${escapeHtml(log.description || '')}</td>
                <td>${escapeHtml(log.ip_address || 'N/A')}</td>
                <td>${date}</td>
            </tr>
        `;
    }).join('');
}

// Filter activity logs
function filterActivityLogs() {
    displayActivityLogs(activityLogs);
}

// Populate activity type filter
function populateActivityTypeFilter(logs) {
    const select = document.getElementById('activity-type-filter');
    if (!select) return;
    
    const types = [...new Set(logs.map(log => log.activity_type).filter(Boolean))].sort();
    const currentValue = select.value;
    
    select.innerHTML = '<option value="">All Types</option>' +
        types.map(type => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join('');
    
    if (currentValue) {
        select.value = currentValue;
    }
}

// Download activity logs as CSV
function downloadActivityLogs() {
    const csv = [
        ['ID', 'User', 'Activity Type', 'Description', 'IP Address', 'Date'].join(','),
        ...activityLogs.map(log => [
            log.id,
            `"${(log.username || 'N/A').replace(/"/g, '""')}"`,
            `"${(log.activity_type || 'Unknown').replace(/"/g, '""')}"`,
            `"${(log.description || '').replace(/"/g, '""')}"`,
            `"${(log.ip_address || 'N/A').replace(/"/g, '""')}"`,
            `"${formatDateUTC5(log.created_at)}"`
        ].join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Download analytics report
function downloadAnalytics() {
    if (!analyticsData) {
        alert('Analytics data not loaded yet. Please wait...');
        return;
    }
    
    const report = {
        generated_at: new Date().toISOString(),
        security_events: analyticsData.security_events,
        activity_logs: analyticsData.activity_logs,
        users: analyticsData.users,
        failed_logins: analyticsData.failed_logins
    };
    
    const json = JSON.stringify(report, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security_analytics_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// Load chat messages
function loadChatMessages() {
    fetch('/blue-team/chat/messages', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayChatMessages(data.data || []);
        } else {
            console.error('Error loading chat messages:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading chat messages:', error);
    });
}

// Display chat messages
function displayChatMessages(messages) {
    const container = document.getElementById('chat-messages');
    
    if (messages.length === 0) {
        container.innerHTML = `
            <div class="chat-empty">
                <i class="bx bx-message-dots"></i>
                <p>No messages yet. Start a conversation with the admin.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        const date = formatDateUTC5(msg.created_at);
        const isAdmin = msg.is_from_admin;
        return `
            <div class="chat-message ${isAdmin ? 'admin' : 'user'}">
                <div class="chat-message-header">
                    <span><strong>${isAdmin ? 'Admin' : 'You'}</strong></span>
                    <span>${date}</span>
                </div>
                <div class="chat-message-text">${escapeHtml(msg.message)}</div>
            </div>
        `;
    }).join('');
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Send chat message
function sendChatMessage() {
    const input = document.getElementById('chat-message-input');
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    const formData = new FormData();
    formData.append('message', message);
    
    fetch('/blue-team/chat/send', {
        method: 'POST',
        credentials: 'include',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.value = '';
            loadChatMessages();
        } else {
            alert('Error: ' + (data.error || 'Failed to send message'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Error sending message');
    });
}

// Allow Enter key to send message
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-message-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
});

// Load RoboPets Analytics
function loadRoboPetsAnalytics() {
    fetch('/blue-team/robopets-analytics', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateRoboPetsStats(data.data);
            updateRoboPetsCharts(data.data);
        } else {
            console.error('Error loading RoboPets analytics:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading RoboPets analytics:', error);
    });
}

// Update RoboPets stats
function updateRoboPetsStats(data) {
    document.getElementById('total-robots').textContent = data.total_robots || 0;
    document.getElementById('available-robots').textContent = data.available_robots || 0;
    document.getElementById('booked-robots').textContent = data.booked_robots || 0;
    document.getElementById('maintenance-robots').textContent = data.maintenance_robots || 0;
    document.getElementById('total-bookings-all').textContent = data.total_bookings || 0;
    document.getElementById('active-users-with-robots').textContent = data.active_users_with_robots || 0;
    document.getElementById('bookings-24h').textContent = data.bookings_24h || 0;
    document.getElementById('bookings-7d').textContent = data.bookings_7d || 0;
}

// Update RoboPets charts
function updateRoboPetsCharts(data) {
    // Robot Status Chart
    const statusCtx = document.getElementById('robotStatusChart');
    if (statusCtx && data.status_breakdown) {
        if (charts.robotStatus) {
            charts.robotStatus.destroy();
        }
        charts.robotStatus = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data.status_breakdown),
                datasets: [{
                    data: Object.values(data.status_breakdown),
                    backgroundColor: [
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(234, 179, 8, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(59, 130, 246, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });
    }

    // Booking Activity Chart
    const bookingCtx = document.getElementById('bookingActivityChart');
    if (bookingCtx && data.booking_timeline) {
        if (charts.bookingActivity) {
            charts.bookingActivity.destroy();
        }
        charts.bookingActivity = new Chart(bookingCtx, {
            type: 'line',
            data: {
                labels: data.booking_timeline.map(d => d.date),
                datasets: [{
                    label: 'Bookings',
                    data: data.booking_timeline.map(d => d.count),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: {
                            color: '#e2e8f0'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    // Popular Robots Chart
    const popularCtx = document.getElementById('popularRobotsChart');
    if (popularCtx && data.popular_robots) {
        if (charts.popularRobots) {
            charts.popularRobots.destroy();
        }
        const topRobots = data.popular_robots.slice(0, 10);
        charts.popularRobots = new Chart(popularCtx, {
            type: 'bar',
            data: {
                labels: topRobots.map(r => r.name),
                datasets: [{
                    label: 'Bookings',
                    data: topRobots.map(r => r.booking_count),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

// Download RoboPets Analytics
function downloadRoboPetsAnalytics() {
    fetch('/blue-team/robopets-analytics', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const report = {
                generated_at: new Date().toISOString(),
                ...data.data
            };
            const json = JSON.stringify(report, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `robopets_analytics_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            window.URL.revokeObjectURL(url);
        }
    })
    .catch(error => {
        console.error('Error downloading RoboPets analytics:', error);
        alert('Error downloading analytics');
    });
}

// Load GCP Logs
let autoRefreshInterval = null;

function loadGCPLogs() {
    const level = document.getElementById('log-level-filter')?.value || '';
    const service = document.getElementById('log-service-filter')?.value || '';
    const limit = parseInt(document.getElementById('log-limit')?.value || 50);

    let url = `/blue-team/gcp-logs?limit=${limit}`;
    if (level) url += `&level=${level}`;
    if (service) url += `&service=${service}`;

    fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            displayGCPLogs(data.data || []);
        } else {
            console.error('Error loading GCP logs:', data.error);
            document.getElementById('gcp-logs-tbody').innerHTML = 
                '<tr><td colspan="5" class="loading">Error loading logs: ' + (data.error || 'Unknown error') + '</td></tr>';
        }
    })
    .catch(error => {
        console.error('Error loading GCP logs:', error);
        document.getElementById('gcp-logs-tbody').innerHTML = 
            '<tr><td colspan="5" class="loading">Error loading logs. Please check if GCP Logging API is enabled.</td></tr>';
    });
}

// Display GCP Logs
function displayGCPLogs(logs) {
    const tbody = document.getElementById('gcp-logs-tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No logs found</td></tr>';
        return;
    }
    
    // Store logs data in a global array for event handlers
    if (!window.gcpLogsData) {
        window.gcpLogsData = [];
    }
    window.gcpLogsData = logs.map((log, index) => ({
        id: log.id || index,
        message: log.message || '',
        level: log.severity || 'INFO',
        service: log.service || 'default',
        details: log.details ? JSON.stringify(log.details, null, 2) : ''
    }));
    
    tbody.innerHTML = logs.map((log, index) => {
        const timestamp = formatDateUTC5(log.timestamp);
        const level = log.severity || 'INFO';
        const levelClass = level.toLowerCase();
        const message = log.message || '';
        const messageEscaped = escapeHtml(message);
        const details = log.details ? JSON.stringify(log.details, null, 2) : '';
        const detailsEscaped = escapeHtml(details).replace(/'/g, "\\'").replace(/\n/g, '\\n');
        const service = log.service || 'default';
        const serviceEscaped = escapeHtml(service);
        
        // Use index as ID if log doesn't have one
        const logId = log.id || index;
        
        return `
            <tr>
                <td>${timestamp}</td>
                <td><span class="severity-badge ${levelClass}">${level}</span></td>
                <td>${serviceEscaped}</td>
                <td style="max-width: 400px; word-wrap: break-word;">${messageEscaped}</td>
                <td>
                    <div style="display: flex; gap: 5px; flex-wrap: wrap;">
                        ${details ? `
                        <button class="action-btn log-details-btn" data-index="${index}" style="font-size: 11px; padding: 4px 8px; cursor: pointer;">
                            <i class="bx bx-info-circle"></i> Details
                        </button>
                        ` : ''}
                        <button class="action-btn mark-threat-btn" 
                                data-index="${index}"
                                style="font-size: 11px; padding: 4px 8px; background: linear-gradient(135deg, #ef4444, #dc2626); color: white; cursor: pointer; border: none;">
                            <i class="bx bx-shield-x"></i> Mark as Threat
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Use event delegation on the tbody - remove old listener first
    const newTbody = document.getElementById('gcp-logs-tbody');
    if (newTbody) {
        // Remove any existing click handlers
        const newHandler = function(e) {
            const target = e.target.closest('.mark-threat-btn');
            if (target) {
                e.preventDefault();
                e.stopPropagation();
                const index = parseInt(target.getAttribute('data-index'));
                const logData = window.gcpLogsData[index];
                if (logData) {
                    console.log('Button clicked, showing threat severity selector');
                    showThreatSeveritySelector(logData);
                } else {
                    console.error('Log data not found for index:', index);
                    alert('Error: Could not find log data');
                }
                return false;
            }
            
            const detailsBtn = e.target.closest('.log-details-btn');
            if (detailsBtn) {
                e.preventDefault();
                e.stopPropagation();
                const index = parseInt(detailsBtn.getAttribute('data-index'));
                const logData = window.gcpLogsData[index];
                if (logData && logData.details) {
                    showLogDetails(logData.details);
                }
                return false;
            }
        };
        
        // Remove old listener and add new one
        newTbody.removeEventListener('click', newTbody._clickHandler);
        newTbody._clickHandler = newHandler;
        newTbody.addEventListener('click', newHandler);
    }
}

// Show log details
function showLogDetails(details) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.7); z-index: 10000; display: flex;
        align-items: center; justify-content: center; padding: 20px;
    `;
    modal.innerHTML = `
        <div style="background: var(--dark-bg); border: 1px solid var(--glass-border);
        border-radius: 16px; padding: 25px; max-width: 800px; max-height: 80vh;
        overflow-y: auto; width: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: var(--text-primary);">Log Details</h3>
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" 
                        style="background: var(--danger); color: white; border: none;
                        padding: 8px 16px; border-radius: 8px; cursor: pointer;">
                    <i class="bx bx-x"></i> Close
                </button>
            </div>
            <pre style="background: rgba(30, 58, 138, 0.2); padding: 15px; border-radius: 8px;
            color: var(--text-primary); overflow-x: auto; font-size: 12px;">${escapeHtml(details)}</pre>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Toggle auto-refresh
function toggleAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh-logs');
    if (checkbox.checked) {
        autoRefreshInterval = setInterval(loadGCPLogs, 30000); // 30 seconds
    } else {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    }
}

// Mark GCP log as threat
// Show severity selector modal
function showThreatSeveritySelector(logData) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.7); z-index: 10000; display: flex;
        align-items: center; justify-content: center; padding: 20px;
    `;
    
    const messagePreview = (logData.message || '').substring(0, 150);
    
    modal.innerHTML = `
        <div style="background: var(--dark-bg); border: 1px solid var(--glass-border);
        border-radius: 16px; padding: 25px; max-width: 600px; width: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: var(--text-primary); margin: 0;">
                    <i class="bx bx-shield-x"></i> Mark as Security Threat
                </h3>
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" 
                        style="background: none; border: none; color: var(--text-secondary); 
                        font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px;">
                    &times;
                </button>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 8px; color: var(--text-primary); font-weight: 600;">
                    Log Message:
                </label>
                <div style="padding: 12px; background: rgba(30, 58, 138, 0.2); border-radius: 8px; 
                    border: 1px solid var(--glass-border); color: var(--text-secondary); 
                    font-size: 13px; max-height: 100px; overflow-y: auto;">
                    ${escapeHtml(messagePreview)}${logData.message && logData.message.length > 150 ? '...' : ''}
                </div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 10px; color: var(--text-primary); font-weight: 600;">
                    Select Threat Severity:
                </label>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button class="severity-option" data-severity="critical" 
                            style="padding: 15px; background: linear-gradient(135deg, #ef4444, #dc2626); 
                            color: white; border: 2px solid #ef4444; border-radius: 8px; cursor: pointer;
                            font-weight: 600; transition: all 0.3s;">
                        <i class="bx bx-error-circle"></i><br>Critical
                    </button>
                    <button class="severity-option" data-severity="high" 
                            style="padding: 15px; background: linear-gradient(135deg, #f59e0b, #d97706); 
                            color: white; border: 2px solid #f59e0b; border-radius: 8px; cursor: pointer;
                            font-weight: 600; transition: all 0.3s;">
                        <i class="bx bx-error"></i><br>High
                    </button>
                    <button class="severity-option" data-severity="medium" 
                            style="padding: 15px; background: linear-gradient(135deg, #3b82f6, #2563eb); 
                            color: white; border: 2px solid #3b82f6; border-radius: 8px; cursor: pointer;
                            font-weight: 600; transition: all 0.3s;">
                        <i class="bx bx-info-circle"></i><br>Medium
                    </button>
                    <button class="severity-option" data-severity="low" 
                            style="padding: 15px; background: linear-gradient(135deg, #10b981, #059669); 
                            color: white; border: 2px solid #10b981; border-radius: 8px; cursor: pointer;
                            font-weight: 600; transition: all 0.3s;">
                        <i class="bx bx-check-circle"></i><br>Low
                    </button>
                </div>
                <div style="margin-top: 15px; padding: 12px; background: rgba(59, 130, 246, 0.1); 
                    border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <div style="font-size: 12px; color: var(--text-secondary);">
                        <strong>Note:</strong> Only <strong>High</strong> and <strong>Critical</strong> threats 
                        will be visible to Admin in the Security Threats tab.
                    </div>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" 
                        style="padding: 10px 20px; background: var(--card-bg); color: var(--text-primary);
                        border: 1px solid var(--border-color); border-radius: 8px; cursor: pointer;">
                    Cancel
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add hover effects
    modal.querySelectorAll('.severity-option').forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = 'none';
        });
        btn.addEventListener('click', function() {
            const severity = this.getAttribute('data-severity');
            modal.remove();
            markLogAsThreat(logData.id, logData.message, logData.level, logData.service, severity);
        });
    });
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function markLogAsThreat(logId, message, level, service, severity) {
    console.log('markLogAsThreat called with:', { logId, message, level, service, severity });
    
    // Ensure message is a string
    let fullMessage = String(message || '');
    
    // Validate inputs
    if (!fullMessage) {
        alert('Error: No message to mark as threat');
        return;
    }
    
    if (!level) {
        level = 'INFO';
    }
    
    if (!service) {
        service = 'default';
    }
    
    // Validate severity
    if (!severity || !['low', 'medium', 'high', 'critical'].includes(severity)) {
        severity = 'medium'; // Default to medium if not provided
    }
    
    const requestBody = {
        log_id: logId,
        message: fullMessage,
        level: level,
        service: service,
        severity: severity
    };
    
    console.log('Sending request:', requestBody);
    
    fetch('/blue-team/gcp-logs/mark-threat', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Error response:', text);
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.status === 'success') {
            let message = 'Log entry marked as security threat successfully!';
            if (severity === 'high' || severity === 'critical') {
                message += '\n\n⚠️ This threat has been escalated to Admin and will appear in the Admin Security Threats tab.';
            } else {
                message += '\n\nThis threat will appear in the Security Events tab (visible to Blue Team only).';
            }
            alert(message);
            // Refresh security events if that tab is active
            if (document.getElementById('security-events-tab') && document.getElementById('security-events-tab').classList.contains('active')) {
                loadSecurityEvents();
            }
            // Also refresh analytics to show updated counts
            loadAnalytics();
        } else {
            alert('Error: ' + (data.error || 'Failed to mark as threat'));
        }
    })
    .catch(error => {
        console.error('Error marking log as threat:', error);
        alert('Error marking log as threat: ' + error.message);
    });
}

// Utility function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format date to UTC-5 (EST/EDT timezone)
function formatDateUTC5(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    // Subtract 5 hours (18000 seconds = 5 hours in milliseconds)
    const utc5Date = new Date(date.getTime() - (5 * 60 * 60 * 1000));
    return utc5Date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
}

