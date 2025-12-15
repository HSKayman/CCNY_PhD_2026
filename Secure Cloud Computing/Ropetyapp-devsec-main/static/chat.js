// Chat Widget JavaScript for User Page

let chatMessages = [];
let chatPollInterval = null;
let isChatOpen = false;
let lastMessageId = 0;
let chatSearchQuery = '';
let filteredMessages = [];

// Initialize chat widget
document.addEventListener('DOMContentLoaded', function() {
    const chatToggleBtn = document.getElementById('chatToggleBtn');
    const chatCloseBtn = document.getElementById('chatCloseBtn');
    const chatBox = document.getElementById('chatBox');
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    const chatEmojiBtn = document.getElementById('chatEmojiBtn');
    const chatSearchBtn = document.getElementById('chatSearchBtn');
    const chatSearchInput = document.getElementById('chatSearchInput');
    const chatSearchContainer = document.getElementById('chatSearchContainer');
    const chatSearchClose = document.getElementById('chatSearchClose');
    
    if (!chatToggleBtn || !chatBox) {
        return; // Chat widget not on this page
    }
    
    // Toggle chat
    chatToggleBtn.addEventListener('click', function() {
        isChatOpen = !isChatOpen;
        if (isChatOpen) {
            chatBox.classList.add('open');
            loadChatMessages();
            startChatPolling();
            chatInput.focus();
        } else {
            chatBox.classList.remove('open');
            stopChatPolling();
            // Close emoji picker and search when closing chat
            if (chatEmojiPicker) chatEmojiPicker.style.display = 'none';
            if (chatSearchContainer) chatSearchContainer.style.display = 'none';
        }
    });
    
    // Close chat
    if (chatCloseBtn) {
        chatCloseBtn.addEventListener('click', function() {
            isChatOpen = false;
            chatBox.classList.remove('open');
            stopChatPolling();
        });
    }
    
    // Emoji picker
    if (chatEmojiBtn) {
        chatEmojiBtn.addEventListener('click', function() {
            const emojiPicker = document.getElementById('chatEmojiPicker');
            if (emojiPicker) {
                emojiPicker.style.display = emojiPicker.style.display === 'none' ? 'block' : 'none';
            }
        });
        
        // Close emoji picker when clicking outside
        document.addEventListener('click', function(e) {
            const emojiPicker = document.getElementById('chatEmojiPicker');
            if (emojiPicker && !emojiPicker.contains(e.target) && e.target !== chatEmojiBtn) {
                emojiPicker.style.display = 'none';
            }
        });
        
        // Emoji selection
        document.querySelectorAll('.emoji-item').forEach(item => {
            item.addEventListener('click', function() {
                const emoji = this.getAttribute('data-emoji');
                if (chatInput && emoji) {
                    chatInput.value += emoji;
                    chatInput.focus();
                }
            });
        });
    }
    
    // Search functionality
    if (chatSearchBtn && chatSearchContainer) {
        chatSearchBtn.addEventListener('click', function() {
            chatSearchContainer.style.display = chatSearchContainer.style.display === 'none' ? 'flex' : 'none';
            if (chatSearchInput) {
                setTimeout(() => chatSearchInput.focus(), 100);
            }
        });
    }
    
    if (chatSearchClose) {
        chatSearchClose.addEventListener('click', function() {
            if (chatSearchContainer) chatSearchContainer.style.display = 'none';
            if (chatSearchInput) {
                chatSearchInput.value = '';
                chatSearchQuery = '';
                displayChatMessages(); // Show all messages
            }
        });
    }
    
    if (chatSearchInput) {
        chatSearchInput.addEventListener('input', function() {
            chatSearchQuery = this.value.toLowerCase().trim();
            searchChatMessages();
        });
        
        chatSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                chatSearchQuery = '';
                chatSearchContainer.style.display = 'none';
                displayChatMessages();
            }
        });
    }
    
    // Send message on Enter
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
    
    // Send message on button click
    if (chatSendBtn) {
        chatSendBtn.addEventListener('click', function() {
            sendChatMessage();
        });
    }
    
    // Load messages on page load
    loadChatMessages();
    startChatPolling();
});

// Load chat messages
function loadChatMessages() {
    fetch('/chat/messages', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: ''
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            chatMessages = data.data || [];
            lastMessageId = chatMessages.length > 0 ? chatMessages[chatMessages.length - 1].id : 0;
            displayChatMessages();
            updateChatBadge(data.unread_count || 0);
        }
    })
    .catch(error => {
        console.error('Error loading chat messages:', error);
    });
}

// Search chat messages
function searchChatMessages() {
    if (!chatSearchQuery) {
        displayChatMessages();
        return;
    }
    
    filteredMessages = chatMessages.filter(msg => 
        msg.message.toLowerCase().includes(chatSearchQuery)
    );
    
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    if (filteredMessages.length === 0) {
        messagesContainer.innerHTML = `<div class="chat-empty">No messages found matching "${escapeHtml(chatSearchQuery)}"</div>`;
        return;
    }
    
    messagesContainer.innerHTML = filteredMessages.map(msg => {
        const date = new Date(msg.created_at);
        const time = formatChatTime(date);
        const isUser = !msg.is_from_admin;
        
        // Highlight search query in message
        let highlightedMessage = escapeHtml(msg.message);
        const regex = new RegExp(`(${escapeHtml(chatSearchQuery)})`, 'gi');
        highlightedMessage = highlightedMessage.replace(regex, '<mark>$1</mark>');
        
        return `
            <div class="chat-message ${isUser ? 'user' : 'admin'}">
                <div class="message-bubble">${highlightedMessage}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
    }).join('');
}

// Display chat messages
function displayChatMessages() {
    const messagesContainer = document.getElementById('chatMessages');
    if (!messagesContainer) return;
    
    if (chatSearchQuery) {
        searchChatMessages();
        return;
    }
    
    if (chatMessages.length === 0) {
        messagesContainer.innerHTML = '<div class="chat-empty">No messages yet. Start a conversation!</div>';
        return;
    }
    
    messagesContainer.innerHTML = chatMessages.map(msg => {
        const date = new Date(msg.created_at);
        const time = formatChatTime(date);
        const isUser = !msg.is_from_admin;
        
        return `
            <div class="chat-message ${isUser ? 'user' : 'admin'}">
                <div class="message-bubble">${escapeHtml(msg.message)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;
    }).join('');
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Format time for chat
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

// Validate chat message on client side
function validateChatMessage(message) {
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

// Send chat message
function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatSendBtn = document.getElementById('chatSendBtn');
    
    if (!chatInput || !chatSendBtn) return;
    
    const message = chatInput.value;
    
    // Validate message
    const validation = validateChatMessage(message);
    if (!validation.valid) {
        alert(validation.error);
        return;
    }
    
    // Disable input while sending
    chatInput.disabled = true;
    chatSendBtn.disabled = true;
    
    const formData = new URLSearchParams();
    formData.append('message', message.trim());
    
    fetch('/chat/send', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            chatInput.value = '';
            // Reload messages to show the new one
            loadChatMessages();
        } else {
            alert('Error: ' + (data.error || 'Failed to send message'));
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        alert('Error sending message. Please try again.');
    })
    .finally(() => {
        chatInput.disabled = false;
        chatSendBtn.disabled = false;
        chatInput.focus();
    });
}

// Start polling for new messages
function startChatPolling() {
    if (chatPollInterval) return;
    
    chatPollInterval = setInterval(() => {
        if (isChatOpen) {
            checkForNewMessages();
        } else {
            // Still check for new messages when closed to update badge
            loadChatMessages();
        }
    }, 3000); // Poll every 3 seconds
}

// Stop polling
function stopChatPolling() {
    if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
    }
}

// Check for new messages
function checkForNewMessages() {
    fetch('/chat/messages', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: ''
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const newMessages = data.data || [];
            
            // Check if there are new messages
            if (newMessages.length > chatMessages.length || 
                (newMessages.length > 0 && newMessages[newMessages.length - 1].id > lastMessageId)) {
                chatMessages = newMessages;
                lastMessageId = newMessages.length > 0 ? newMessages[newMessages.length - 1].id : 0;
                displayChatMessages();
            }
            
            updateChatBadge(data.unread_count || 0);
        }
    })
    .catch(error => {
        console.error('Error checking for new messages:', error);
    });
}

// Update chat badge
function updateChatBadge(unreadCount) {
    const badge = document.getElementById('chatBadge');
    if (!badge) return;
    
    if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Escape HTML
function escapeHtml(text) {
    if (text == null || text === undefined) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

