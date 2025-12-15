// static/script.js
// This frontend relies entirely on server-side HttpOnly cookie authentication.
// No sessionStorage or localStorage is used for tokens - all auth is handled via cookies.

const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const filterField = document.getElementById("search-field");
// Get logout button - check both on page load and later
let logoutBtn = document.getElementById("logout-p");

const errorField = document.getElementById("errorText");
const nameText = document.getElementById("username-display");
const filteredList = document.getElementById("filtered-list");
const userRobotContainer = document.getElementById("user-robot");

// Store robots data globally
let allRobotsData = [];
let userRobotsData = [];
let currentFilter = "";

// ==================== PASSWORD VISIBILITY TOGGLE ====================
function initPasswordToggles() {
  const togglePassword1 = document.getElementById("togglePassword");
  const togglePassword2 = document.getElementById("togglePassword1");
  const togglePassword3 = document.getElementById("togglePassword2");
  
  const passwordInput1 = document.getElementById("password");
  const passwordInput2 = document.getElementById("password_1");
  const passwordInput3 = document.getElementById("password_2");

  if (togglePassword1 && passwordInput1) {
    togglePassword1.addEventListener("click", () => {
      const type = passwordInput1.getAttribute("type") === "password" ? "text" : "password";
      passwordInput1.setAttribute("type", type);
      togglePassword1.querySelector("svg").style.opacity = type === "password" ? "1" : "0.5";
    });
  }

  if (togglePassword2 && passwordInput2) {
    togglePassword2.addEventListener("click", () => {
      const type = passwordInput2.getAttribute("type") === "password" ? "text" : "password";
      passwordInput2.setAttribute("type", type);
      togglePassword2.querySelector("svg").style.opacity = type === "password" ? "1" : "0.5";
    });
  }

  if (togglePassword3 && passwordInput3) {
    togglePassword3.addEventListener("click", () => {
      const type = passwordInput3.getAttribute("type") === "password" ? "text" : "password";
      passwordInput3.setAttribute("type", type);
      togglePassword3.querySelector("svg").style.opacity = type === "password" ? "1" : "0.5";
    });
  }
}

// ==================== GOOGLE reCAPTCHA ====================
// Google reCAPTCHA is handled automatically by the widget
// The token is included in the form submission automatically
// No client-side validation needed - server verifies the token

// ==================== DARK MODE ====================
function initDarkMode() {
  const darkModeToggle = document.getElementById("darkModeToggle");
  if (!darkModeToggle) return;

  // Load saved theme - default to dark mode for user page
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  darkModeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  });
}

// ==================== ALPHABET FILTER ====================
function initAlphabetFilter() {
  const alphabetFilter = document.getElementById("alphabetFilter");
  if (!alphabetFilter) return;

  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  
  alphabet.split("").forEach((letter) => {
    const btn = document.createElement("button");
    btn.className = "alphabet-btn";
    btn.textContent = letter;
    btn.setAttribute("data-letter", letter);
    btn.addEventListener("click", () => {
      // Toggle active state
      document.querySelectorAll(".alphabet-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      
      // Filter by letter
      filterByLetter(letter);
    });
    alphabetFilter.appendChild(btn);
  });
}

function filterByLetter(letter) {
  currentFilter = letter.toLowerCase();
  // Update search field to show the filter
  if (filterField) {
    filterField.value = letter;
  }
  // Clear active state from all buttons
  document.querySelectorAll(".alphabet-btn").forEach((b) => b.classList.remove("active"));
  // Set active state on clicked button
  event.target.classList.add("active");
  filterPetList(currentFilter);
}

// ==================== USER PAGE INITIALIZATION ====================
if (nameText) {
  fetch("/getusername", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: '',
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.username) {
        nameText.innerText = data.username;
        // Update welcome message with username
        const welcomeUsername = document.getElementById('welcome-username');
        if (welcomeUsername) {
          welcomeUsername.innerText = data.username;
        }
      } else {
        window.location.href = "/login";
      }
    })
    .catch(() => {
      window.location.href = "/login";
    });
  
  // Initialize dark mode
  initDarkMode();
  
  // Initialize logout button
  initLogoutButton();
  
  // Initialize search button
  initSearchButton();
}

// ==================== LOAD ROBOTS ====================
// Function to load robots and user robots together
function loadRobotsAndUserRobots() {
  // Load both in parallel
  Promise.all([
    fetch("/getallrobots", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: '',
    }).then(r => r.json()),
    fetch("/getuserrobots", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: '',
    }).then(r => {
      if (!r.ok) return { status: "success", data: [] };
      return r.json();
    }).then(data => {
      // Handle both old format {robots: []} and new format {status: "success", data: []}
      if (data.robots) return { status: "success", data: data.robots };
      if (data.status === "success" && data.data) return { status: "success", data: data.data };
      return { status: "success", data: [] };
    }).catch(() => ({ status: "success", data: [] }))
  ]).then(([robotsData, userRobotsData]) => {
    if (robotsData.all_robots) {
      allRobotsData = robotsData.all_robots;
    }
    
    // Extract user robots array - handle both formats
    let userRobotsArray = [];
    if (userRobotsData && userRobotsData.status === "success" && Array.isArray(userRobotsData.data)) {
      userRobotsArray = userRobotsData.data;
    } else if (userRobotsData && userRobotsData.robots && Array.isArray(userRobotsData.robots)) {
      userRobotsArray = userRobotsData.robots;
    } else if (Array.isArray(userRobotsData)) {
      userRobotsArray = userRobotsData;
    }
    
    // Store globally for use in other functions
    userRobotsData = userRobotsArray;
    
    if (filteredList) {
      // Apply current filter if any
      if (currentFilter && currentFilter.trim() !== "") {
        filterPetList(currentFilter);
      } else {
        updateRobotList(filteredList, allRobotsData, userRobotsArray);
      }
    }
    
    // Update user's robot display
    if (userRobotContainer) {
      updateCurrentPets(userRobotsArray);
    }
  }).catch(err => {
    console.error("Error loading robots:", err);
    if (filteredList) {
      updateRobotList(filteredList, [], []);
    }
    });
}

if (filteredList) {
  loadRobotsAndUserRobots();
  // Alerts polling will start in DOMContentLoaded to prevent duplicates
}

// ==================== ALERTS FUNCTIONALITY ====================
// Declare variables at the top level to avoid initialization errors
var lastAlertCount = 0;
var alertsPollInterval = null;
var isPollingActive = false; // Flag to prevent duplicate polling
var isFirstLoad = true; // Track if this is the first load
var errorBackoffDelay = 3000; // Start with 3 seconds, will increase on errors

function loadAlerts(showNewAlertAnimation = false) {
  // No longer using alertsContainer - alerts are shown as notifications only
  fetch("/getalerts", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: '',
  })
    .then(r => {
      if (!r.ok) {
        // Handle different error statuses
        if (r.status === 500 || r.status === 502) {
          console.warn(`⚠️ Server error ${r.status} fetching alerts, will retry with backoff`);
          // Increase backoff delay on server errors (max 30 seconds)
          errorBackoffDelay = Math.min(errorBackoffDelay * 1.5, 30000);
          
          // If polling is active, restart with longer delay
          if (isPollingActive && alertsPollInterval) {
            clearInterval(alertsPollInterval);
            alertsPollInterval = setInterval(() => {
              loadAlerts(true);
            }, errorBackoffDelay);
            console.log(`Retrying alerts polling with ${errorBackoffDelay/1000}s delay`);
          }
        }
        
        // Try to get error message, but don't fail if JSON parsing fails
        return r.text().then(text => {
          try {
            return Promise.reject(JSON.parse(text));
          } catch {
            return Promise.reject({ error: `Server error: ${r.status}`, status: r.status });
          }
        });
      }
      
      // Reset backoff on success
      errorBackoffDelay = 3000;
      return r.json();
    })
    .then(data => {
      if (data.status === "success") {
        const alerts = data.data || [];
        const unreadCount = data.unread_count || 0;
        
        console.log(`📬 Alerts loaded: ${alerts.length} total, ${unreadCount} unread`);
        
        // On first load, show all unread alerts
        // On subsequent loads, only show new alerts
        const shouldShowAlerts = isFirstLoad ? unreadCount > 0 : (showNewAlertAnimation && unreadCount > lastAlertCount);
        
        if (shouldShowAlerts) {
          const unreadAlerts = alerts.filter(a => !a.read);
          
          if (unreadAlerts.length > 0) {
            if (isFirstLoad) {
              console.log(`🔔 Showing ${unreadAlerts.length} unread alerts on first load`);
              // Show the most recent alert on first load as popup
              const newestAlert = unreadAlerts[0];
              const date = new Date(newestAlert.created_at);
              // Subtract 5 hours (user requested -5hrs)
              date.setHours(date.getHours() - 5);
              const formattedDate = date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
              });
              
              console.log("📢 Displaying first alert notification:", newestAlert.message.substring(0, 50));
              showAlertNotification(
                escapeHtml(newestAlert.message),
                formattedDate
              );
              
              // Show additional alerts after a delay
              if (unreadAlerts.length > 1) {
                setTimeout(() => {
                  showNotification(`You have ${unreadAlerts.length} unread message${unreadAlerts.length > 1 ? 's' : ''}. New alerts will appear here.`, "info", 5000);
                }, 2000);
              }
              
              isFirstLoad = false;
            } else {
              console.log("🔔 New alert detected! Unread count:", unreadCount, "Previous:", lastAlertCount);
              // Show the newest alert as a popup notification
              const newestAlert = unreadAlerts[0];
              const date = new Date(newestAlert.created_at);
              // Subtract 5 hours (user requested -5hrs)
              date.setHours(date.getHours() - 5);
              const formattedDate = date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
              });
              
              console.log("📢 Displaying alert notification:", newestAlert.message.substring(0, 50));
              showAlertNotification(
                escapeHtml(newestAlert.message),
                formattedDate
              );
            }
          }
        }
        
        lastAlertCount = unreadCount;
      }
    })
    .catch(err => {
      // Only log error details, don't spam console
      if (err.status !== 500 && err.status !== 502) {
        console.error("Error loading alerts:", err);
      }
      // Error already handled in .then() for server errors
    });
}

// Start polling for new alerts every 3 seconds for faster real-time updates
function startAlertsPolling() {
  // Prevent duplicate polling
  if (isPollingActive) {
    console.log("Alerts polling already active, skipping duplicate start");
    return;
  }
  
  try {
    // Clear any existing interval first (safety check)
    if (alertsPollInterval !== null && alertsPollInterval !== undefined) {
      clearInterval(alertsPollInterval);
      alertsPollInterval = null;
    }
    
    // Mark as active
    isPollingActive = true;
    
    console.log("Starting alerts polling...");
    
    // Load alerts immediately
    loadAlerts();
    
    // Then poll every 3 seconds for faster real-time delivery
    alertsPollInterval = setInterval(() => {
      loadAlerts(true); // Pass true to show animation for new alerts
    }, errorBackoffDelay); // Use dynamic delay that adjusts on errors
    
    console.log("Alerts polling started, interval ID:", alertsPollInterval);
  } catch (error) {
    console.error("Error starting alerts polling:", error);
    isPollingActive = false;
  }
}

// Stop polling (e.g., when user logs out)
function stopAlertsPolling() {
  if (alertsPollInterval) {
    clearInterval(alertsPollInterval);
    alertsPollInterval = null;
  }
  isPollingActive = false;
  errorBackoffDelay = 3000; // Reset delay
}

function markAlertRead(alertId) {
  const formData = new URLSearchParams();
  formData.append("alert_id", alertId);
  
  // Find the alert item and add fade-out animation
  const alertItem = document.querySelector(`.alert-item[data-alert-id="${alertId}"]`);
  if (alertItem) {
    alertItem.style.transition = 'all 0.3s ease';
    alertItem.style.opacity = '0.5';
    alertItem.style.transform = 'translateX(-20px)';
  }
  
  fetch("/markalertread", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  })
    .then(r => r.json())
    .then(data => {
      if (data.status === "success") {
        // Reload alerts with smooth transition
        setTimeout(() => {
          loadAlerts();
        }, 300);
      }
    })
    .catch(err => {
      console.error("Error marking alert as read:", err);
      // Restore alert item if error
      if (alertItem) {
        alertItem.style.opacity = '1';
        alertItem.style.transform = 'translateX(0)';
      }
    });
}

// ==================== NOTIFICATION SYSTEM ====================
function showNotification(message, type = "info", duration = 3000) {
  // Remove existing notification if any (except alert notifications)
  const existing = document.querySelector('.notification:not(.alert-notification)');
  if (existing) {
    existing.remove();
  }
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <i class="bx ${type === 'success' ? 'bx-check-circle' : type === 'error' ? 'bx-error-circle' : 'bx-info-circle'}"></i>
      <span>${escapeHtml(message)}</span>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Trigger animation
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  // Remove after delay
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, duration);
}

// Special notification function for alerts - shows longer and more prominently
function showAlertNotification(message, dateTime) {
  console.log("🔔 showAlertNotification called with message:", message.substring(0, 50));
  
  // Remove existing alert notification if any (with small delay to allow stacking)
  const existing = document.querySelectorAll('.notification.alert-notification');
  existing.forEach((notif, index) => {
    // Remove older ones but keep the most recent
    if (index < existing.length - 1) {
      notif.remove();
    }
  });
  
  const notification = document.createElement('div');
  notification.className = 'notification notification-info alert-notification';
  notification.innerHTML = `
    <div class="alert-notification-content">
      <div class="alert-notification-icon">
        <i class="bx bx-bell"></i>
      </div>
      <div class="alert-notification-text">
        <div class="alert-notification-message">${message}</div>
        <div class="alert-notification-time">⏰ ${dateTime}</div>
      </div>
    </div>
  `;
  
  // Ensure notification is visible
  notification.style.display = 'block';
  notification.style.visibility = 'visible';
  notification.style.opacity = '1';
  notification.style.zIndex = '99999';
  
  document.body.appendChild(notification);
  console.log("✅ Alert notification added to DOM");
  
  // Force reflow to ensure element is rendered
  notification.offsetHeight;
  
  // Trigger animation immediately
  requestAnimationFrame(() => {
    notification.classList.add('show');
    console.log("✅ Alert notification animation triggered");
  });
  
  // Remove after longer delay (10 seconds for alerts so user has time to read)
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      if (notification.parentNode) {
        notification.remove();
        console.log("✅ Alert notification removed");
      }
    }, 300);
  }, 10000);
}

// Enhanced notification with better visuals for select/return actions
function showEnhancedNotification(message, type = "info", action = "default") {
  // Remove existing notification if any
  const existing = document.querySelector('.notification');
  if (existing) {
    existing.remove();
  }
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type} notification-enhanced notification-${action}`;
  
  // Different icons and styles based on action
  let iconClass = 'bx-check-circle';
  if (action === 'select') {
    iconClass = 'bx-check-circle';
  } else if (action === 'return') {
    iconClass = 'bx-undo';
  }
  
  notification.innerHTML = `
    <div class="notification-content">
      <div class="notification-icon-wrapper">
        <i class="bx ${iconClass}"></i>
      </div>
      <span class="notification-message">${escapeHtml(message)}</span>
    </div>
    <div class="notification-progress"></div>
  `;
  
  document.body.appendChild(notification);
  
  // Trigger enhanced animation
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  // Add confetti effect for success actions
  if (type === 'success' && action === 'select') {
    createConfettiEffect();
  }
  
  // Remove after delay
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 400);
  }, 2500);
}

// Create confetti effect for successful selections
function createConfettiEffect() {
  const colors = ['#6C5CE7', '#0984E3', '#00B894', '#FDCB6E', '#E17055'];
  const confettiCount = 30;
  
  for (let i = 0; i < confettiCount; i++) {
    setTimeout(() => {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = Math.random() * 100 + '%';
      confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDelay = Math.random() * 0.5 + 's';
      confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
      document.body.appendChild(confetti);
      
      setTimeout(() => {
        confetti.remove();
      }, 2000);
    }, i * 20);
  }
}

function escapeHtml(text) {
  if (text == null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

// ==================== LOAD USER ROBOTS (MULTIPLE) ====================
if (userRobotContainer) {
  // Try new endpoint first
  fetch("/getuserrobots", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  })
    .then((r) => {
      if (!r.ok) {
        throw new Error("Endpoint not available");
      }
      return r.json();
    })
    .then((data) => {
      if (data.robots && Array.isArray(data.robots)) {
        userRobotsData = data.robots;
        updateCurrentPets(data.robots);
      } else {
        userRobotsData = [];
        updateCurrentPets([]);
      }
    })
    .catch((err) => {
      console.log("New endpoint not available, trying fallback:", err);
      // Fallback to old endpoint
  fetch("/getuserrobot", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  })
    .then((r) => r.json())
    .then((data) => {
          const robots = data.robot && data.robot.robot_id !== -1 ? [data.robot] : [];
          userRobotsData = robots;
          updateCurrentPets(robots);
        })
        .catch((err) => {
          console.error("Error loading user robots:", err);
          userRobotsData = [];
          updateCurrentPets([]);
        });
    });
}

// ==================== LOGOUT ====================
// Handle logout button click - ensure it's initialized after DOM loads
function initLogoutButton() {
  // Try to get the button again in case it wasn't found initially
  if (!logoutBtn) {
    logoutBtn = document.getElementById("logout-p");
  }
  
  if (logoutBtn) {
    // Remove any existing listeners by cloning and replacing
    const newLogoutBtn = logoutBtn.cloneNode(true);
    logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
    logoutBtn = newLogoutBtn;
    
    logoutBtn.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      console.log("Logout button clicked");
      
      fetch("/logout", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      })
        .then((response) => {
          console.log("Logout response:", response.status);
          // Always redirect to login, regardless of response
          window.location.href = "/login";
        })
        .catch((error) => {
          console.error("Logout error:", error);
          // Even on error, redirect to login
          window.location.href = "/login";
        });
    });
  } else {
    console.warn("Logout button not found");
  }
}

// Initialize logout button when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLogoutButton);
} else {
  initLogoutButton();
}

// ==================== SEARCH FUNCTIONALITY ====================
// Real-time search as user types
filterField?.addEventListener("input", (event) => {
  event.preventDefault();
  currentFilter = event.target.value;
  // Debounce for better performance
  clearTimeout(window.searchTimeout);
  window.searchTimeout = setTimeout(() => {
    filterPetList(currentFilter);
  }, 150); // 150ms delay for real-time search
});

// Search button inside input field
function initSearchButton() {
  const searchBtnInside = document.getElementById("search-btn-inside");
  const searchField = document.getElementById("search-field");
  
  if (searchBtnInside && searchField) {
    searchBtnInside.addEventListener("click", (event) => {
      event.preventDefault();
      if (searchField.value) {
        currentFilter = searchField.value;
        filterPetList(currentFilter);
      }
    });
    
    // Also search on Enter key
    searchField.addEventListener("keypress", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (searchField.value) {
          currentFilter = searchField.value;
          filterPetList(currentFilter);
        }
      }
    });
  }
}

// Search on Enter key
filterField?.addEventListener("keypress", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    if (filterField) {
      currentFilter = filterField.value;
      filterPetList(currentFilter);
    }
  }
});

function filterPetList(filterValue) {
  // Use cached data if available, otherwise reload
  let robotsToFilter = allRobotsData.length > 0 ? allRobotsData : [];
  
  if (robotsToFilter.length === 0) {
    // If no data, reload
    loadRobotsAndUserRobots();
    return;
  }
  
  let filter_robots;
  if (!filterValue || filterValue.trim() === "") {
    filter_robots = robotsToFilter;
  } else {
    const filterLower = filterValue.toLowerCase().trim();
    filter_robots = robotsToFilter.filter((robot) => {
      const name = robot.name.toLowerCase();
      // Prefix search - only matches if name starts with the search text
      return name.startsWith(filterLower);
    });
  }
  
  // Get user's robot IDs to exclude (only show robots user doesn't currently own)
  const userRobotIds = (userRobotsData && Array.isArray(userRobotsData)) 
    ? userRobotsData.map((r) => r.robot_id) 
    : [];
  filter_robots = filter_robots.filter((r) => !userRobotIds.includes(r.robot_id));
  
  updateRobotList(filteredList, filter_robots, userRobotsData);
}

// ==================== UPDATE ROBOT LIST ====================
function updateRobotList(list, robots, userRobots) {
  if (!list) return;
  
  list.innerHTML = "";
  
  if (robots.length === 0) {
    const li = document.createElement("li");
    const p = document.createElement("p");
    p.style.textAlign = "center";
    p.style.color = "var(--text-secondary)";
    p.style.padding = "20px";
    p.textContent = "No robots available";
    li.appendChild(p);
    list.appendChild(li);
    return;
  }
  
  robots.forEach((item) => {
    createPetElement(list, item, userRobots);
  });
}

function createPetElement(listContainer, pet, userRobots) {
  const li = document.createElement("li");
  const div = document.createElement("div");
  div.className = "robopet";
  
  // Create image container with overlay support
  const imgContainer = document.createElement("div");
  imgContainer.className = "robopet-image-container";
  imgContainer.style.position = "relative";
  imgContainer.style.display = "inline-block";
  
  const img = createImageElement(pet.name, "100px");
  imgContainer.appendChild(img);
  
  // Check if robot is booked by someone else
  const isBooked = pet.is_booked === true;
  
  // Add "Already booked" overlay if robot is booked
  if (isBooked) {
    const overlay = document.createElement("div");
    overlay.className = "booked-overlay";
    overlay.style.position = "absolute";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100%";
    overlay.style.height = "100%";
    overlay.style.backgroundColor = "rgba(0, 0, 0, 0.7)";
    overlay.style.display = "flex";
    overlay.style.alignItems = "center";
    overlay.style.justifyContent = "center";
    overlay.style.borderRadius = "8px";
    overlay.style.color = "#fff";
    overlay.style.fontWeight = "bold";
    overlay.style.fontSize = "0.9rem";
    overlay.style.textAlign = "center";
    overlay.style.padding = "5px";
    overlay.innerText = "Already Booked";
    overlay.style.zIndex = "10";
    imgContainer.appendChild(overlay);
    
    // Make image slightly faded
    img.style.opacity = "0.6";
  }
  
  div.appendChild(imgContainer);
  
  const p = createNameElement(pet.name);
  div.appendChild(p);
  
  // Check if user already has this robot
  // userRobots should be an array of objects with robot_id property
  const hasRobot = userRobots && Array.isArray(userRobots) && 
                   userRobots.some((r) => r.robot_id === pet.robot_id);
  
  if (!hasRobot && !isBooked) {
    const button = document.createElement("button");
    button.innerText = "Select";
    button.className = "btn-select";
    button.setAttribute("data-robot-id", pet.robot_id);
    button.addEventListener("click", (e) => {
      e.preventDefault();
      const robotId = parseInt(e.target.getAttribute("data-robot-id"));
      selectUserRobot(robotId);
    });
    div.appendChild(button);
  } else if (hasRobot) {
    const span = document.createElement("span");
    span.innerText = "Selected";
    span.style.color = "var(--success)";
    span.style.fontSize = "0.85rem";
    span.style.fontWeight = "600";
    div.appendChild(span);
  } else if (isBooked) {
    const span = document.createElement("span");
    span.innerText = "Unavailable";
    span.style.color = "#ff6b6b";
    span.style.fontSize = "0.85rem";
    span.style.fontWeight = "600";
    div.appendChild(span);
  }
  
  li.appendChild(div);
  listContainer.appendChild(li);
}

// ==================== UPDATE USER ROBOTS (MULTIPLE) ====================
function updateCurrentPets(robots) {
  if (!userRobotContainer) return;
  
  userRobotContainer.innerHTML = "";
  
  if (!robots || robots.length === 0) {
    const p = document.createElement("p");
    p.className = "empty-state";
    p.innerText = "You don't have any RoboPets yet. Select one from the available list!";
    userRobotContainer.appendChild(p);
    return;
  }
  
  robots.forEach((robot) => {
    if (robot.robot_id === -1) return;
    
    const div = document.createElement("div");
    div.className = "robopet-item";
    
    const img = createImageElement(robot.robot_name, "80px");
    const p = createNameElement(robot.robot_name);
    
    const returnBtn = document.createElement("button");
    returnBtn.className = "return-btn";
    returnBtn.setAttribute("data-robot-id", robot.robot_id);
    returnBtn.innerText = "Return";
    returnBtn.addEventListener("click", () => {
      returnRobot(robot.robot_id);
    });
    
    div.appendChild(img);
    div.appendChild(p);
    div.appendChild(returnBtn);
    userRobotContainer.appendChild(div);
  });
}

// Legacy function for single robot (kept for compatibility)
function updateCurrentPet(robot) {
  updateCurrentPets(robot && robot.robot_id !== -1 ? [robot] : []);
}

// ==================== SELECT ROBOT ====================
function selectUserRobot(robotId) {
  console.log("Selecting robot:", robotId);
  const formData = new URLSearchParams();
  formData.append("robot_id", robotId);
  
  // Find the specific button for this robot
  const button = document.querySelector(`button[data-robot-id="${robotId}"]`);
  const originalText = button ? button.textContent : "Select";
  
  // Disable button to prevent double-clicks
  if (button) {
    button.disabled = true;
    button.textContent = "Selecting...";
  }
  
  fetch("/setuserrobot", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  })
    .then((r) => {
      if (!r.ok) {
        return r.json().then(data => Promise.reject(data));
      }
      return r.json();
    })
    .then((resp) => {
      if (resp.status === "success") {
        // Show enhanced success animation with robot name
        const robotName = button?.closest('.robopet-item')?.querySelector('p')?.textContent || 'RoboPet';
        showEnhancedNotification(`🎉 ${robotName} selected successfully!`, "success", "select");
        // Add visual feedback to the button
        if (button) {
          button.style.background = "var(--success)";
          button.style.transform = "scale(1.1)";
          button.textContent = "✓ Selected!";
        }
        // Reload after a longer delay to show the animation
        setTimeout(() => {
          window.location.reload();
        }, 2500);
      } else {
        console.error("Select failed", resp);
        // Re-enable button
        if (button) {
          button.disabled = false;
          button.textContent = originalText;
        }
        // Show error message
        showNotification(resp.error || "Failed to select robot. It may already be selected by another user.", "error");
      }
    })
    .catch((err) => {
      console.error("Error selecting robot:", err);
      // Re-enable button
      if (button) {
        button.disabled = false;
        button.textContent = originalText;
      }
      showNotification(err.error || "An error occurred while selecting the robot. Please try again.", "error");
    });
}

// ==================== RETURN ROBOT ====================
function returnRobot(robotId) {
  // Show confirmation with custom message
  if (!confirm("Why did you deselect? Are you sure you want to return this robot?")) {
    return;
  }
  
  const formData = new URLSearchParams();
  formData.append("robot_id", robotId);
  
  // Find the return button
  const returnButtons = document.querySelectorAll('.return-btn');
  returnButtons.forEach(btn => {
    if (btn.getAttribute('data-robot-id') == robotId) {
      btn.disabled = true;
      btn.textContent = "Returning...";
    }
  });
  
  fetch("/returnuserrobot", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  })
    .then((r) => {
      if (!r.ok) {
        return r.json().then(data => Promise.reject(data));
      }
      return r.json();
    })
    .then((resp) => {
      if (resp.status === "success") {
        // Show enhanced success animation for return
        const robotItem = document.querySelector(`.robopet-item:has(button[data-robot-id="${robotId}"])`);
        const robotName = robotItem?.querySelector('p')?.textContent || 'RoboPet';
        showEnhancedNotification(`👋 ${robotName} returned successfully!`, "success", "return");
        // Add visual feedback
        if (robotItem) {
          robotItem.style.transition = "all 0.5s ease";
          robotItem.style.opacity = "0.5";
          robotItem.style.transform = "scale(0.95)";
        }
        // Reload after a longer delay to show the animation
        setTimeout(() => {
          window.location.reload();
        }, 2500);
      } else {
        console.error("Return failed", resp);
        // Re-enable buttons
        returnButtons.forEach(btn => {
          if (btn.getAttribute('data-robot-id') == robotId) {
            btn.disabled = false;
            btn.textContent = "Return";
          }
        });
        showNotification(resp.error || "Failed to return robot", "error");
      }
    })
    .catch((err) => {
      console.error("Error returning robot:", err);
      // Re-enable buttons
      returnButtons.forEach(btn => {
        if (btn.getAttribute('data-robot-id') == robotId) {
          btn.disabled = false;
          btn.textContent = "Return";
        }
      });
      showNotification(err.error || "An error occurred while returning the robot", "error");
    });
}

// ==================== HELPER FUNCTIONS ====================
function createNameElement(petName) {
  const p = document.createElement("p");
  // Escape HTML to prevent XSS
  const safeName = escapeHtml(petName || '');
  p.textContent = safeName[0].toUpperCase() + safeName.slice(1);
  return p;
}

function createImageElement(petName, size) {
  const img = document.createElement("img");
  img.setAttribute("class", "robopet");
  // Escape petName in URL to prevent XSS
  const safeName = encodeURIComponent(petName || '');
  img.setAttribute("src", "/getRobotImage/" + safeName + ".png");
  img.setAttribute("alt", escapeHtml(petName || "RoboPet"));
  img.setAttribute("width", size);
  img.setAttribute("height", size);
  img.style.objectFit = "contain";
  return img;
}

// ==================== VALIDATION FUNCTIONS ====================
function validateEmail(email) {
  if (!email || !email.trim()) {
    return { valid: false, error: "Email is required" };
  }
  
  email = email.trim();
  
  // Check length
  if (email.length < 5) {
    return { valid: false, error: "Email is too short" };
  }
  if (email.length > 254) {
    return { valid: false, error: "Email is too long" };
  }
  
  // Must contain exactly one @
  if (email.split('@').length !== 2) {
    return { valid: false, error: "Email must contain exactly one @ symbol" };
  }
  
  const parts = email.split('@');
  const localPart = parts[0];
  const domainPart = parts[1];
  
  // Validate local part
  if (!localPart || localPart.length === 0) {
    return { valid: false, error: "Email must have a local part before @" };
  }
  if (localPart.length > 64) {
    return { valid: false, error: "Email local part is too long" };
  }
  if (localPart.startsWith('.') || localPart.endsWith('.')) {
    return { valid: false, error: "Email local part cannot start or end with a dot" };
  }
  if (localPart.includes('..')) {
    return { valid: false, error: "Email local part cannot contain consecutive dots" };
  }
  
  // Validate domain part
  if (!domainPart || domainPart.length === 0) {
    return { valid: false, error: "Email must have a domain part after @" };
  }
  if (domainPart.startsWith('.') || domainPart.endsWith('.')) {
    return { valid: false, error: "Email domain cannot start or end with a dot" };
  }
  if (domainPart.includes('..')) {
    return { valid: false, error: "Email domain cannot contain consecutive dots" };
  }
  
  // Must have a TLD (at least one dot in domain)
  if (!domainPart.includes('.')) {
    return { valid: false, error: "Email domain must contain a top-level domain (e.g., .com, .org)" };
  }
  
  // Extract TLD
  const tld = domainPart.split('.').pop().toLowerCase();
  
  // TLD must be at least 2 characters and only letters
  if (tld.length < 2) {
    return { valid: false, error: "Email must have a valid top-level domain (e.g., .com, .org)" };
  }
  if (!/^[a-z]+$/.test(tld)) {
    return { valid: false, error: "Email top-level domain must contain only letters" };
  }
  
  // Basic email pattern check
  const emailPattern = /^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    return { valid: false, error: "Email format is invalid. Please use a valid email address" };
  }
  
  return { valid: true, error: "" };
}

function validateUsername(username) {
  if (!username || !username.trim()) {
    return { valid: false, error: "Username is required" };
  }
  
  username = username.trim();
  
  if (username.length < 3) {
    return { valid: false, error: "Username must be at least 3 characters long" };
  }
  if (username.length > 30) {
    return { valid: false, error: "Username must be no more than 30 characters long" };
  }
  
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    return { valid: false, error: "Username can only contain letters, numbers, underscores, and hyphens" };
  }
  
  if (username.startsWith('_') || username.startsWith('-')) {
    return { valid: false, error: "Username cannot start with underscore or hyphen" };
  }
  if (username.endsWith('_') || username.endsWith('-')) {
    return { valid: false, error: "Username cannot end with underscore or hyphen" };
  }
  
  return { valid: true, error: "" };
}

// ==================== SIGNUP FORM ====================
signupForm?.addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const email = formData.get("email");
  const username = formData.get("username");
  const password_1 = formData.get("password_1");
  const password_2 = formData.get("password_2");

  // Validate email
  const emailValidation = validateEmail(email);
  if (!emailValidation.valid) {
    errorField.innerText = emailValidation.error;
    return;
  }
  
  // Validate username
  const usernameValidation = validateUsername(username);
  if (!usernameValidation.valid) {
    errorField.innerText = usernameValidation.error;
    return;
  }
  
  if (!password_1) {
    errorField.innerText = "Please enter a password";
    return;
  }
  if (password_1 !== password_2) {
    errorField.innerText = "Passwords do not match";
    return;
  }

  fetch("/usersignup", {
    method: "POST",
    credentials: "include",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => Promise.reject(data.error || "Signup failed"));
      }
      return response.json();
    })
    .then((data) => {
      if (data.username) {
        window.location.href = `/user/${encodeURIComponent(data.username)}`;
      } else {
        window.location.href = "/user";
      }
    })
    .catch((error) => {
      errorField.innerText = "Authentication failed: " + error;
    });
});

// ==================== LOGIN FORM ====================
loginForm?.addEventListener("submit", function (event) {
  event.preventDefault();
  
  const formData = new FormData(event.target);
  
  // Get reCAPTCHA response if enabled
  if (window.recaptchaEnabled && typeof grecaptcha !== 'undefined' && grecaptcha) {
    // Try to get response - if using explicit render, need widget ID
    let recaptchaResponse = null;
    let widgetFound = false;
    
    // Check if widget element exists
    const widgetElement = document.getElementById('recaptcha-widget');
    const recaptchaWidget = widgetElement || document.querySelector('.g-recaptcha');
    
    if (recaptchaWidget) {
      widgetFound = true;
      
      try {
        // Strategy 1: Use stored widget ID (most reliable for explicit render)
        if (window.recaptchaWidgetId !== null && window.recaptchaWidgetId !== undefined) {
          recaptchaResponse = grecaptcha.getResponse(window.recaptchaWidgetId);
          console.log("reCAPTCHA: Got response using stored widget ID:", window.recaptchaWidgetId);
        }
        
        // Strategy 2: Try data attribute widget ID
        if ((!recaptchaResponse || recaptchaResponse === "") && widgetElement && widgetElement.dataset && widgetElement.dataset.widgetId) {
          const widgetId = parseInt(widgetElement.dataset.widgetId);
          recaptchaResponse = grecaptcha.getResponse(widgetId);
          console.log("reCAPTCHA: Got response using data attribute widget ID:", widgetId);
        }
        
        // Strategy 3: Try all widget IDs (if multiple exist)
        if (!recaptchaResponse || recaptchaResponse === "") {
          try {
            // Get all rendered widgets
            let widgetId = 0;
            while (widgetId < 10) {  // Try up to 10 widget IDs
              try {
                const response = grecaptcha.getResponse(widgetId);
                if (response && response !== "") {
                  recaptchaResponse = response;
                  console.log("reCAPTCHA: Got response using widget ID:", widgetId);
                  break;
                }
              } catch (e) {
                // Widget ID doesn't exist, continue
              }
              widgetId++;
            }
          } catch (e) {
            console.warn("reCAPTCHA: Error trying widget IDs:", e);
          }
        }
        
        // Strategy 4: Fallback - try without ID (for implicit render)
        if (!recaptchaResponse || recaptchaResponse === "") {
          try {
            recaptchaResponse = grecaptcha.getResponse();
            console.log("reCAPTCHA: Got response without widget ID");
          } catch (e) {
            console.warn("reCAPTCHA: Could not get response without widget ID:", e);
          }
        }
        
      } catch (e) {
        console.error("reCAPTCHA: Error getting response:", e);
      }
    }
    
    if (recaptchaResponse && recaptchaResponse.trim() !== "") {
      formData.append("g-recaptcha-response", recaptchaResponse);
      console.log("✓ reCAPTCHA response added to form (length:", recaptchaResponse.length, ")");
    } else if (widgetFound) {
      // Widget exists but no response - user hasn't completed it
      console.warn("⚠ reCAPTCHA widget found but response is empty - user needs to complete it");
      errorField.innerText = "Please complete the reCAPTCHA verification before submitting.";
      event.preventDefault(); // Prevent form submission
      return;
    } else {
      // No widget found - reCAPTCHA might not be enabled or loaded yet
      console.log("ℹ reCAPTCHA not enabled or widget not found");
    }
  }

  const email = formData.get("email");
  const password = formData.get("password");
  
  // Validate email
  const emailValidation = validateEmail(email);
  if (!emailValidation.valid) {
    errorField.innerText = emailValidation.error;
    if (window.recaptchaEnabled && typeof grecaptcha !== 'undefined' && grecaptcha) {
      try { grecaptcha.reset(); } catch(e) {}
    }
    return;
  }
  
  if (!password || !password.trim()) {
    errorField.innerText = "Password is required";
    if (window.recaptchaEnabled && typeof grecaptcha !== 'undefined' && grecaptcha) {
      try { grecaptcha.reset(); } catch(e) {}
    }
    return;
  }
  
  if (password.length > 128) {
    errorField.innerText = "Password is too long";
    if (window.recaptchaEnabled && typeof grecaptcha !== 'undefined' && grecaptcha) {
      try { grecaptcha.reset(); } catch(e) {}
    }
    return;
  }

  fetch("/userlogin", {
    method: "POST",
    credentials: "include",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        return response.json().then((data) => Promise.reject(data.error || "Invalid credentials"));
      }
      return response.json();
    })
    .then((data) => {
      // Check if 2FA is required
      if (data.status === "2fa_required") {
        // Hide login form and show 2FA form
        const loginForm = document.getElementById("loginForm");
        const twoFactorSection = document.getElementById("twoFactorSection");
        if (loginForm) loginForm.style.display = "none";
        if (twoFactorSection) twoFactorSection.style.display = "block";
        if (errorField) errorField.innerText = "";
        // Focus on 2FA input
        const totpInput = document.getElementById("totpCode");
        if (totpInput) totpInput.focus();
        return;
      }
      
      // Normal login success
      if (data.username) {
        window.location.href = `/user/${encodeURIComponent(data.username)}`;
      } else {
        window.location.href = "/user";
      }
    })
    .catch((error) => {
      errorField.innerText = "Authentication failed: " + error;
      if (window.recaptchaEnabled && typeof grecaptcha !== 'undefined' && grecaptcha) {
        try { grecaptcha.reset(); } catch(e) {}
      }
    });
});

// ==================== 2FA FORM ====================
const twoFactorForm = document.getElementById("twoFactorForm");
const cancel2FABtn = document.getElementById("cancel2FA");

if (twoFactorForm) {
  twoFactorForm.addEventListener("submit", function (event) {
    event.preventDefault();
    
    let code = document.getElementById("totpCode").value.trim();
    // Remove any spaces or dashes from the code
    code = code.replace(/\s+/g, '').replace(/-/g, '');
    
    if (!code || (code.length !== 6 && code.length !== 8)) {
      if (errorField) errorField.innerText = "Please enter a valid 6-digit code or 8-digit backup code";
      return;
    }
    
    const formData = new FormData();
    formData.append("code", code);
    
    fetch("/verify-2fa", {
      method: "POST",
      credentials: "include",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((data) => Promise.reject(data.error || "Invalid code"));
        }
        return response.json();
      })
      .then((data) => {
        if (data.username) {
          window.location.href = `/user/${encodeURIComponent(data.username)}`;
        } else {
          window.location.href = "/user";
        }
      })
      .catch((error) => {
        if (errorField) errorField.innerText = "Verification failed: " + error;
        // Clear the input
        const totpInput = document.getElementById("totpCode");
        if (totpInput) {
          totpInput.value = "";
          totpInput.focus();
        }
      });
  });
}

if (cancel2FABtn) {
  cancel2FABtn.addEventListener("click", function () {
    // Show login form and hide 2FA form
    const loginForm = document.getElementById("loginForm");
    const twoFactorSection = document.getElementById("twoFactorSection");
    if (loginForm) loginForm.style.display = "block";
    if (twoFactorSection) twoFactorSection.style.display = "none";
    if (errorField) errorField.innerText = "";
    // Reload page to clear session
    window.location.reload();
  });
}

// Auto-format 2FA code input (only numbers, max 8 digits for backup codes)
const totpCodeInput = document.getElementById("totpCode");
if (totpCodeInput) {
  totpCodeInput.addEventListener("input", function (e) {
    // Only allow numbers
    e.target.value = e.target.value.replace(/[^0-9]/g, '');
    // Limit to 8 digits (6 for TOTP, 8 for backup codes)
    if (e.target.value.length > 8) {
      e.target.value = e.target.value.slice(0, 8);
    }
  });
  
  // Auto-submit when 6 digits are entered (TOTP code) or 8 digits (backup code)
  totpCodeInput.addEventListener("input", function (e) {
    const value = e.target.value.replace(/\s+/g, '').replace(/-/g, '');
    if (value.length === 6 || value.length === 8) {
      setTimeout(() => {
        if (twoFactorForm) {
          twoFactorForm.dispatchEvent(new Event('submit'));
        }
      }, 300);
    }
  });
}

// ==================== BOOKING HISTORY ====================
function loadBookingHistory() {
  const container = document.getElementById('bookingHistoryContainer');
  if (!container) return;
  
  fetch('/booking-history?limit=5', {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      displayBookingHistory(data.data || []);
    }
  })
  .catch(error => {
    console.error('Error loading booking history:', error);
    if (container) {
      container.innerHTML = '<div class="announcements-loading">Error loading booking history</div>';
    }
  });
}

function displayBookingHistory(bookings) {
  const container = document.getElementById('bookingHistoryContainer');
  if (!container) return;
  
  if (bookings.length === 0) {
    container.innerHTML = '<div class="announcements-loading">No booking history</div>';
    return;
  }
  
  container.innerHTML = bookings.slice(0, 5).map(booking => {
    const pickedDate = booking.picked_at ? (() => {
      const date = new Date(booking.picked_at);
      date.setHours(date.getHours() - 5); // Subtract 5 hours
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    })() : 'N/A';
    const duration = booking.duration_hours ? `${booking.duration_hours}h` : 'Ongoing';
    const statusClass = booking.status === 'active' ? 'active' : 'completed';
    
    return `
      <div class="booking-history-item" style="padding: 10px; margin-bottom: 10px; background: var(--bg-secondary); border-radius: 8px; border: 1px solid var(--border-color);">
        <div style="display: flex; align-items: center; gap: 10px;">
          ${booking.robot_image ? `<img src="${booking.robot_image}" alt="${booking.robot_name}" style="width: 40px; height: 40px; border-radius: 8px; object-fit: cover;">` : ''}
          <div style="flex: 1;">
            <strong>${booking.robot_name || 'Unknown'}</strong>
            <div style="font-size: 0.9em; color: var(--text-secondary);">
              ${pickedDate} • ${duration}
              <span style="margin-left: 10px; padding: 2px 8px; background: ${statusClass === 'active' ? '#00B894' : '#636E72'}; color: white; border-radius: 4px; font-size: 0.8em;">
                ${statusClass}
              </span>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// View all bookings button
document.addEventListener('DOMContentLoaded', function() {
  const viewAllBtn = document.getElementById('viewAllBookingsBtn');
  if (viewAllBtn) {
    viewAllBtn.addEventListener('click', function() {
      // Show all bookings in a modal or new section
      fetch('/booking-history?limit=50', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          const allBookings = data.data || [];
          const bookingList = allBookings.map(b => 
            `${b.robot_name} - ${(() => {
              const date = new Date(b.picked_at);
              date.setHours(date.getHours() - 5); // Subtract 5 hours
              return date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
              });
            })()} (${b.duration_hours ? b.duration_hours + 'h' : 'Ongoing'})`
          ).join('\n');
          alert('All Bookings:\n\n' + (bookingList || 'No bookings'));
        }
      })
      .catch(error => console.error('Error:', error));
    });
  }
});

// ==================== USER STATISTICS ====================
function loadUserStatistics() {
  const container = document.getElementById('userStatsContainer');
  if (!container) return;
  
  fetch('/user/statistics', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: ''
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Statistics data received:', data);
    if (data.status === 'success' && data.data) {
      displayUserStatistics(data.data);
    } else {
      console.error('Statistics response error:', data);
      container.innerHTML = '<div class="stats-loading">Unable to load statistics</div>';
    }
  })
  .catch(error => {
    console.error('Error loading statistics:', error);
    container.innerHTML = '<div class="stats-loading">Error loading statistics. Please refresh the page.</div>';
  });
}

function displayUserStatistics(stats) {
  const container = document.getElementById('userStatsContainer');
  if (!container) {
    console.error('Stats container not found');
    return;
  }
  
  if (!stats) {
    console.error('No stats data provided');
    container.innerHTML = '<div class="stats-loading">No statistics available</div>';
    return;
  }
  
  const favoriteRobot = stats.favorite_robot || 'None yet';
  const accountAge = stats.account_age_days !== undefined ? stats.account_age_days : 0;
  const accountAgeText = accountAge === 0 ? 'Today' : accountAge === 1 ? '1 day' : `${accountAge} days`;
  
  container.innerHTML = `
    <div class="stat-card">
      <div class="stat-value">${stats.current_robots !== undefined ? stats.current_robots : 0}</div>
      <div class="stat-label">Current Robots</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.total_robots_selected !== undefined ? stats.total_robots_selected : 0}</div>
      <div class="stat-label">Total Selected</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.total_booking_hours !== undefined ? stats.total_booking_hours : 0}h</div>
      <div class="stat-label">Booking Time</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.total_bookings !== undefined ? stats.total_bookings : 0}</div>
      <div class="stat-label">Total Bookings</div>
    </div>
    <div class="stat-card" style="grid-column: 1 / -1;">
      <div class="stat-value" style="font-size: 1.2rem;">⭐ ${escapeHtml(favoriteRobot)}</div>
      <div class="stat-label">Favorite Robot</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${accountAgeText}</div>
      <div class="stat-label">Member Since</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${stats.login_count !== undefined ? stats.login_count : 0}</div>
      <div class="stat-label">Logins</div>
    </div>
  `;
}

// ==================== ACTIVITY FEED ====================
function loadActivityFeed() {
  const container = document.getElementById('activityContainer');
  if (!container) return;
  
  fetch('/user/activity?limit=10', {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success' && data.data) {
      displayActivityFeed(data.data);
    } else {
      container.innerHTML = '<div class="activity-loading">No recent activity</div>';
    }
  })
  .catch(error => {
    console.error('Error loading activity:', error);
    container.innerHTML = '<div class="activity-loading">Error loading activity</div>';
  });
}

function displayActivityFeed(activities) {
  const container = document.getElementById('activityContainer');
  if (!container) return;
  
  if (activities.length === 0) {
    container.innerHTML = '<div class="activity-loading">No recent activity</div>';
    return;
  }
  
  container.innerHTML = activities.map(activity => {
    const date = new Date(activity.created_at);
    date.setHours(date.getHours() - 5); // Adjust timezone
    const timeAgo = getTimeAgo(date);
    
    let iconClass = 'bx-time-five';
    let activityClass = 'login';
    if (activity.activity_type === 'Booking') {
      iconClass = 'bx-check-circle';
      activityClass = 'booking';
    } else if (activity.activity_type === 'Return') {
      iconClass = 'bx-undo';
      activityClass = 'return';
    }
    
    return `
      <div class="activity-item">
        <div class="activity-icon ${activityClass}">
          <i class="bx ${iconClass}"></i>
        </div>
        <div class="activity-content">
          <div class="activity-description">${escapeHtml(activity.description || activity.activity_type)}</div>
          <div class="activity-time">${timeAgo}</div>
        </div>
      </div>
    `;
  }).join('');
}

function getTimeAgo(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ==================== ROBOT DETAILS MODAL ====================
function showRobotDetails(robotId, robotName) {
  const modal = document.getElementById('robotModalOverlay');
  const modalBody = document.getElementById('modalBody');
  const modalTitle = document.getElementById('modalRobotName');
  
  if (!modal || !modalBody || !modalTitle) return;
  
  // Set title
  modalTitle.textContent = robotName || 'Robot Details';
  
  // Show loading
  modalBody.innerHTML = '<div style="text-align: center; padding: 40px;">Loading robot details...</div>';
  modal.style.display = 'flex';
  
  // Fetch robot details (we'll use the robot name to get image)
  const robotImage = `/getRobotImage/${encodeURIComponent(robotName)}.png`;
  
  // For now, show basic info. In the future, you could add more details from backend
  modalBody.innerHTML = `
    <div class="robot-detail-item">
      <img src="${robotImage}" alt="${escapeHtml(robotName)}" onerror="this.style.display='none'">
    </div>
    <div class="robot-detail-item">
      <div class="robot-detail-label">Name</div>
      <div class="robot-detail-value">${escapeHtml(robotName)}</div>
    </div>
    <div class="robot-detail-item">
      <div class="robot-detail-label">Status</div>
      <div class="robot-detail-value">Available</div>
    </div>
  `;
}

function closeRobotModal() {
  const modal = document.getElementById('robotModalOverlay');
  if (modal) {
    modal.style.display = 'none';
  }
}

function initRobotModal() {
  const modal = document.getElementById('robotModalOverlay');
  const closeBtn = document.getElementById('modalCloseBtn');
  const okBtn = document.getElementById('modalOkBtn');
  
  if (closeBtn) {
    closeBtn.addEventListener('click', closeRobotModal);
  }
  
  if (okBtn) {
    okBtn.addEventListener('click', closeRobotModal);
  }
  
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeRobotModal();
      }
    });
  }
  
  // Add click handlers to robot images/names
  document.addEventListener('click', (e) => {
    const robotElement = e.target.closest('.robopet');
    if (robotElement) {
      const robotName = robotElement.querySelector('p')?.textContent;
      if (robotName) {
        showRobotDetails(null, robotName);
      }
    }
  });
}

// ==================== SORTING AND FILTERING ====================
function initSortFilter() {
  const sortFilter = document.getElementById('sortFilter');
  if (!sortFilter) return;
  
  sortFilter.addEventListener('change', (e) => {
    const sortValue = e.target.value;
    sortRobotList(sortValue);
  });
}

function sortRobotList(sortType) {
  if (!allRobotsData || allRobotsData.length === 0) {
    loadRobotsAndUserRobots();
    return;
  }
  
  let sortedRobots = [...allRobotsData];
  
  switch(sortType) {
    case 'name-asc':
      sortedRobots.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'name-desc':
      sortedRobots.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case 'popular':
      // For now, just sort by name. In future, could sort by booking count
      sortedRobots.sort((a, b) => a.name.localeCompare(b.name));
      break;
  }
  
  // Get user's robot IDs to exclude
  const userRobotIds = (userRobotsData && Array.isArray(userRobotsData)) 
    ? userRobotsData.map((r) => r.robot_id) 
    : [];
  sortedRobots = sortedRobots.filter((r) => !userRobotIds.includes(r.robot_id));
  
  // Apply current filter if any
  if (currentFilter && currentFilter.trim() !== "") {
    const filterLower = currentFilter.toLowerCase().trim();
    sortedRobots = sortedRobots.filter((robot) => {
      const name = robot.name.toLowerCase();
      return name.startsWith(filterLower);
    });
  }
  
  updateRobotList(filteredList, sortedRobots, userRobotsData);
}

// ==================== VIEW TOGGLE ====================
function initViewToggle() {
  const gridBtn = document.getElementById('viewAsGridBtn');
  const listBtn = document.getElementById('viewAsListBtn');
  const listContainer = document.getElementById('robopetListContainer');
  
  if (!gridBtn || !listBtn || !listContainer) return;
  
  gridBtn.addEventListener('click', () => {
    gridBtn.classList.add('active');
    listBtn.classList.remove('active');
    listContainer.classList.remove('list-view');
    listContainer.classList.add('grid-view');
  });
  
  listBtn.addEventListener('click', () => {
    listBtn.classList.add('active');
    gridBtn.classList.remove('active');
    listContainer.classList.remove('grid-view');
    listContainer.classList.add('list-view');
  });
}

// ==================== INITIALIZE ON LOAD ====================
document.addEventListener("DOMContentLoaded", () => {
  initPasswordToggles();
  // Google reCAPTCHA initializes automatically via script tag
  
  // Load booking history
  loadBookingHistory();
  
  // Load new features
  loadActivityFeed();
  initRobotModal();
  initSortFilter();
  initViewToggle();
  
  // Load 2FA status if on user page
  if (document.getElementById('2fa-status-container')) {
    load2FAStatus();
    init2FAHandlers();
  }
  
  // Check 2FA status and prompt setup if not enabled
  if (document.querySelector('.tabs-container-user')) {
    checkAndPrompt2FASetup();
  }
  
  // Initialize tabs if on user page
  if (document.querySelector('.tabs-container-user')) {
    initUserTabs();
  }
  
  // Start alerts polling if on user page (shows alerts as notifications)
  // Only start once - check if polling is already active
  if (document.getElementById('search-field') && typeof startAlertsPolling === 'function' && !isPollingActive) {
    // Small delay to ensure page is fully loaded
    setTimeout(() => {
      startAlertsPolling();
    }, 500);
  }
});

// ==================== USER TABS FUNCTIONALITY ====================
function initUserTabs() {
  const tabButtons = document.querySelectorAll('.tab-btn-user');
  const tabContents = document.querySelectorAll('.tab-content-user');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const targetTab = button.getAttribute('data-tab');
      
      // Remove active class from all buttons and contents
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      
      // Add active class to clicked button and corresponding content
      button.classList.add('active');
      const targetContent = document.getElementById(`${targetTab}-tab`);
      if (targetContent) {
        targetContent.classList.add('active');
      }
      
      // Load content when tab is switched
      if (targetTab === 'activity') {
        loadActivityFeed();
      } else if (targetTab === 'bookings') {
        loadBookingHistory();
      } else if (targetTab === 'settings') {
        // 2FA status is already loaded, but refresh it
        if (document.getElementById('2fa-status-container')) {
          load2FAStatus();
        }
        // Initialize password change handlers
        initPasswordChangeHandlers();
      }
    });
  });
}

// ==================== 2FA SETUP PROMPT ====================

function checkAndPrompt2FASetup() {
  // Always check 2FA status on login - show prompt every time if 2FA is not enabled
  // (No dismissal check - prompt shows on every login until 2FA is enabled)
  
  // Check 2FA status
  fetch('/api/2fa/status', {
    method: 'GET',
    credentials: 'include'
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success' && !data.data.two_factor_enabled) {
        // 2FA is not enabled, show prompt (every time they log in)
        show2FASetupPrompt();
      }
    })
    .catch(error => {
      console.error('Error checking 2FA status:', error);
    });
}

function show2FASetupPrompt() {
  // Create modal overlay
  const modal = document.createElement('div');
  modal.id = '2fa-setup-prompt-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(5px);
    z-index: 10000;
    display: flex;
    justify-content: center;
    align-items: center;
    animation: fadeIn 0.3s ease;
  `;
  
  // Create modal content
  const modalContent = document.createElement('div');
  modalContent.style.cssText = `
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 40px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    text-align: center;
    animation: slideUp 0.3s ease;
  `;
  
  modalContent.innerHTML = `
    <div style="font-size: 4rem; margin-bottom: 20px;">🔒</div>
    <h2 style="color: #2D3436; margin-bottom: 15px; font-size: 1.8rem; font-weight: 700;">Secure Your Account</h2>
    <p style="color: #636E72; margin-bottom: 30px; line-height: 1.6; font-size: 1rem;">
      Two-factor authentication (2FA) adds an extra layer of security to your account. 
      We recommend enabling it to protect your account from unauthorized access.
    </p>
    <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
      <button id="2fa-setup-now-btn" style="
        padding: 14px 28px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
      ">
        Set Up 2FA Now
      </button>
      <button id="2fa-setup-later-btn" style="
        padding: 14px 28px;
        background: rgba(255, 255, 255, 0.9);
        color: #2D3436;
        border: 2px solid #E0E0E0;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
      ">
        Maybe Later
      </button>
    </div>
  `;
  
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
  
  // Add hover effects
  const setupBtn = document.getElementById('2fa-setup-now-btn');
  const laterBtn = document.getElementById('2fa-setup-later-btn');
  
  setupBtn.addEventListener('mouseenter', () => {
    setupBtn.style.transform = 'translateY(-2px)';
    setupBtn.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
  });
  setupBtn.addEventListener('mouseleave', () => {
    setupBtn.style.transform = 'translateY(0)';
    setupBtn.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
  });
  
  laterBtn.addEventListener('mouseenter', () => {
    laterBtn.style.background = 'rgba(255, 255, 255, 0.95)';
    laterBtn.style.transform = 'translateY(-2px)';
  });
  laterBtn.addEventListener('mouseleave', () => {
    laterBtn.style.background = 'rgba(255, 255, 255, 0.8)';
    laterBtn.style.transform = 'translateY(0)';
  });
  
  // Handle "Set Up Now" button
  setupBtn.addEventListener('click', () => {
    // Close modal
    modal.remove();
    // Switch to Settings tab and trigger 2FA setup
    const settingsTab = document.querySelector('.tab-btn-user[data-tab="settings"]');
    if (settingsTab) {
      settingsTab.click();
      // Wait a bit for tab to switch, then trigger 2FA enable
      setTimeout(() => {
        const enableBtn = document.getElementById('2fa-toggle-btn');
        if (enableBtn && enableBtn.textContent.trim() === 'Enable 2FA') {
          enableBtn.click();
        }
      }, 300);
    }
  });
  
  // Handle "Maybe Later" button
  laterBtn.addEventListener('click', () => {
    // Just close the modal - it will show again on next login
    modal.remove();
  });
  
  // Close on background click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      // Just close the modal - it will show again on next login
      modal.remove();
    }
  });
  
  // Add CSS animations
  if (!document.getElementById('2fa-modal-styles')) {
    const style = document.createElement('style');
    style.id = '2fa-modal-styles';
    style.textContent = `
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from {
          opacity: 0;
          transform: translateY(30px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    document.head.appendChild(style);
  }
}

// ==================== 2FA MANAGEMENT ====================

function load2FAStatus() {
  const container = document.getElementById('2fa-status-container');
  if (!container) return;
  
  fetch('/api/2fa/status', {
    method: 'GET',
    credentials: 'include'
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        const isEnabled = data.data.two_factor_enabled;
        const backupCodesCount = data.data.backup_codes_count || 0;
        
        container.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div>
              <p style="margin: 0; font-weight: 600; color: var(--text-primary);">
                ${isEnabled ? '<i class="bx bx-check-circle" style="color: var(--success);"></i> Enabled' : '<i class="bx bx-x-circle" style="color: var(--text-secondary);"></i> Disabled'}
              </p>
              ${isEnabled && backupCodesCount > 0 ? `<p style="margin: 5px 0 0 0; font-size: 12px; color: var(--text-secondary);">${backupCodesCount} backup code(s) remaining</p>` : ''}
            </div>
            <div style="display: flex; gap: 10px;">
              ${isEnabled && backupCodesCount > 0 ? `
                <button id="2fa-download-backup-btn" class="btn-primary" style="padding: 8px 16px; background: var(--success); color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; display: flex; align-items: center; gap: 5px;">
                  <i class="bx bx-download"></i> Download Backup Codes
                </button>
              ` : ''}
              <button id="2fa-toggle-btn" class="btn-primary" style="padding: 8px 16px; background: ${isEnabled ? 'var(--error)' : 'var(--primary-purple)'}; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                ${isEnabled ? 'Disable 2FA' : 'Enable 2FA'}
              </button>
            </div>
          </div>
          <p style="font-size: 12px; color: var(--text-secondary); margin-top: 10px;">
            Two-factor authentication adds an extra layer of security to your account. 
            You'll need to enter a code from your authenticator app when logging in.
          </p>
        `;
        
        // Add download button handler if 2FA is enabled
        if (isEnabled && backupCodesCount > 0) {
          const downloadBtn = document.getElementById('2fa-download-backup-btn');
          if (downloadBtn) {
            downloadBtn.addEventListener('click', downloadBackupCodes);
          }
        }
        
        // Re-attach event listener
        const toggleBtn = document.getElementById('2fa-toggle-btn');
        if (toggleBtn) {
          toggleBtn.addEventListener('click', () => {
            if (isEnabled) {
              showDisable2FAForm();
            } else {
              startEnable2FA();
            }
          });
        }
      }
    })
    .catch(error => {
      container.innerHTML = '<p style="color: var(--error);">Failed to load 2FA status</p>';
      console.error('2FA status error:', error);
    });
}

function startEnable2FA() {
  fetch('/api/2fa/generate', {
    method: 'POST',
    credentials: 'include'
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Show QR code
        document.getElementById('2fa-qr-code').src = data.data.qr_code;
        document.getElementById('2fa-enable-form').style.display = 'block';
        
        // Store secret for later use
        window.temp2FASecret = data.data.secret;
      } else {
        show2FANotification('Failed to generate 2FA secret', 'error');
      }
    })
    .catch(error => {
      show2FANotification('Error generating 2FA secret', 'error');
      console.error('2FA generate error:', error);
    });
}

function enable2FA() {
  const code = document.getElementById('2fa-verification-code').value.trim();
  if (!code || code.length !== 6) {
    show2FANotification('Please enter a valid 6-digit code', 'error');
    return;
  }
  
  if (!window.temp2FASecret) {
    show2FANotification('2FA setup error. Please try again.', 'error');
    return;
  }
  
  const formData = new FormData();
  formData.append('secret', window.temp2FASecret);
  formData.append('verification_code', code);
  
  fetch('/api/2fa/enable', {
    method: 'POST',
    credentials: 'include',
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        // Show backup codes
        showBackupCodes(data.data.backup_codes);
        // Hide enable form
        document.getElementById('2fa-enable-form').style.display = 'none';
        // Reload status
        load2FAStatus();
        show2FANotification('2FA enabled successfully!', 'success');
      } else {
        show2FANotification(data.error || 'Failed to enable 2FA', 'error');
      }
    })
    .catch(error => {
      show2FANotification('Error enabling 2FA', 'error');
      console.error('2FA enable error:', error);
    });
}

function showDisable2FAForm() {
  document.getElementById('2fa-disable-form').style.display = 'block';
}

function disable2FA() {
  const password = document.getElementById('2fa-disable-password').value;
  if (!password) {
    show2FANotification('Please enter your password', 'error');
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
        document.getElementById('2fa-disable-form').style.display = 'none';
        document.getElementById('2fa-disable-password').value = '';
        load2FAStatus();
        show2FANotification('2FA disabled successfully', 'success');
      } else {
        show2FANotification(data.error || 'Failed to disable 2FA', 'error');
      }
    })
    .catch(error => {
      show2FANotification('Error disabling 2FA', 'error');
      console.error('2FA disable error:', error);
    });
}

function showBackupCodes(codes) {
  const container = document.getElementById('2fa-backup-codes-list');
  container.innerHTML = codes.map(code => `<div style="padding: 5px 0; border-bottom: 1px solid var(--border-color);">${code}</div>`).join('');
  document.getElementById('2fa-backup-codes').style.display = 'block';
  
  // Store codes for download
  window.currentBackupCodes = codes;
}

function downloadBackupCodes() {
  // Try to get codes from current display or fetch from server
  let codes = window.currentBackupCodes;
  
  if (!codes || codes.length === 0) {
    // Fetch from server if not available
    fetch('/api/2fa/backup-codes', {
      method: 'GET',
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success' && data.data.backup_codes) {
          codes = data.data.backup_codes;
          downloadBackupCodesFile(codes);
        } else {
          show2FANotification('No backup codes available', 'error');
        }
      })
      .catch(error => {
        console.error('Error fetching backup codes:', error);
        show2FANotification('Error fetching backup codes', 'error');
      });
  } else {
    downloadBackupCodesFile(codes);
  }
}

function downloadBackupCodesFile(codes) {
  if (!codes || codes.length === 0) {
    show2FANotification('No backup codes to download', 'error');
    return;
  }
  
  // Create file content
  const content = `RoboPety - Two-Factor Authentication Backup Codes

IMPORTANT: Keep these codes in a safe place!
Each code can only be used once.

Backup Codes:
${codes.map((code, index) => `${index + 1}. ${code}`).join('\n')}

Generated: ${new Date().toLocaleString()}

Instructions:
- Use these codes if you lose access to your authenticator app
- Each code can only be used once
- After using a code, it will be removed from your account
- If you use all codes, you'll need to disable and re-enable 2FA to get new ones
`;
  
  // Create blob and download
  const blob = new Blob([content], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `robopety-backup-codes-${new Date().toISOString().split('T')[0]}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
  
  show2FANotification('Backup codes downloaded successfully!', 'success');
}

// Helper function for 2FA notifications (uses existing showNotification)
function show2FANotification(message, type = 'info') {
  if (typeof showNotification === 'function') {
    showNotification(message, type, 5000);
  } else {
    alert(message);
  }
}

function init2FAHandlers() {
  // Enable 2FA button
  const enableBtn = document.getElementById('2fa-enable-btn');
  if (enableBtn) {
    enableBtn.addEventListener('click', enable2FA);
  }
  
  // Cancel enable
  const cancelEnableBtn = document.getElementById('2fa-cancel-enable-btn');
  if (cancelEnableBtn) {
    cancelEnableBtn.addEventListener('click', () => {
      document.getElementById('2fa-enable-form').style.display = 'none';
      document.getElementById('2fa-verification-code').value = '';
      window.temp2FASecret = null;
    });
  }
  
  // Disable 2FA button
  const disableBtn = document.getElementById('2fa-disable-btn');
  if (disableBtn) {
    disableBtn.addEventListener('click', disable2FA);
  }
  
  // Cancel disable
  const cancelDisableBtn = document.getElementById('2fa-cancel-disable-btn');
  if (cancelDisableBtn) {
    cancelDisableBtn.addEventListener('click', () => {
      document.getElementById('2fa-disable-form').style.display = 'none';
      document.getElementById('2fa-disable-password').value = '';
    });
  }
  
  // Download backup codes
  const backupCodesDownload = document.getElementById('2fa-backup-codes-download');
  if (backupCodesDownload) {
    backupCodesDownload.addEventListener('click', downloadBackupCodes);
  }
  
  // Close backup codes
  const backupCodesClose = document.getElementById('2fa-backup-codes-close');
  if (backupCodesClose) {
    backupCodesClose.addEventListener('click', () => {
      document.getElementById('2fa-backup-codes').style.display = 'none';
      window.currentBackupCodes = null; // Clear stored codes
    });
  }
  
  // Auto-format verification code input
  const verificationInput = document.getElementById('2fa-verification-code');
  if (verificationInput) {
    verificationInput.addEventListener('input', (e) => {
      e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 6);
      if (e.target.value.length === 6) {
        // Auto-submit when 6 digits entered
        enable2FA();
      }
    });
  }
}
