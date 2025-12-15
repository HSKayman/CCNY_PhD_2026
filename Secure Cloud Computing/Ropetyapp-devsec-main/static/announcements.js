// Announcements JavaScript for User Page

let announcements = [];
let announcementsPollInterval = null;
let lastAnnouncementId = 0;

// Initialize announcements
document.addEventListener('DOMContentLoaded', function() {
    const announcementsContainer = document.getElementById('announcementsContainer');
    if (!announcementsContainer) {
        return; // Announcements section not on this page
    }
    
    loadAnnouncements();
    startAnnouncementsPolling();
});

// Load announcements from server
function loadAnnouncements() {
    fetch('/announcements', {
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
            announcements = data.data || [];
            displayAnnouncements();
        } else {
            console.error('Failed to load announcements:', data);
            showAnnouncementsError();
        }
    })
    .catch(error => {
        console.error('Error loading announcements:', error);
        showAnnouncementsError();
    });
}

// Display announcements
function displayAnnouncements() {
    const container = document.getElementById('announcementsContainer');
    if (!container) return;
    
    if (announcements.length === 0) {
        container.innerHTML = '<div class="announcements-empty">No upcoming events at this time.</div>';
        return;
    }
    
    // Sort by created_at (newest first)
    const sortedAnnouncements = [...announcements].sort((a, b) => {
        return new Date(b.created_at) - new Date(a.created_at);
    });
    
    container.innerHTML = sortedAnnouncements.map(ann => {
        const date = new Date(ann.created_at);
        const formattedDate = formatAnnouncementDate(date);
        const isNew = ann.id > lastAnnouncementId;
        
        return `
            <div class="announcement-item ${isNew ? 'new' : ''}">
                <div class="announcement-title">
                    <i class="bx bx-info-circle"></i>
                    ${escapeHtml(ann.title)}
                </div>
                <div class="announcement-message">${escapeHtml(ann.message)}</div>
                <div class="announcement-date">${formattedDate}</div>
            </div>
        `;
    }).join('');
    
    // Update last announcement ID
    if (sortedAnnouncements.length > 0) {
        lastAnnouncementId = Math.max(...sortedAnnouncements.map(a => a.id));
    }
}

// Format announcement date and time to Eastern Time (EST/EDT - GMT-5/GMT-4)
// Format: "H:MM AM/PM MM/DD/YYYY" (time first, then date) - Windows taskbar format
function formatAnnouncementDate(date) {
    // Format time in Eastern Time (America/New_York = EST/EDT)
    const timeFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York', // Automatically uses EST (GMT-5) or EDT (GMT-4) based on DST
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
    
    // Format date in Eastern Time
    const dateFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York', // Automatically uses EST (GMT-5) or EDT (GMT-4) based on DST
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
}

// Show error message
function showAnnouncementsError() {
    const container = document.getElementById('announcementsContainer');
    if (container) {
        container.innerHTML = '<div class="announcements-empty">Unable to load announcements. Please refresh the page.</div>';
    }
}

// Start polling for new announcements
function startAnnouncementsPolling() {
    // Poll every 30 seconds for new announcements
    if (announcementsPollInterval) {
        clearInterval(announcementsPollInterval);
    }
    
    announcementsPollInterval = setInterval(() => {
        loadAnnouncements();
    }, 30000); // 30 seconds
}

// Stop polling
function stopAnnouncementsPolling() {
    if (announcementsPollInterval) {
        clearInterval(announcementsPollInterval);
        announcementsPollInterval = null;
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

