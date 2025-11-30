// ===== CONFIGURATION =====
const API_BASE = '';  // Same origin
let currentUser = null;
let currentChatId = null;
let authToken = null;

// ===== INITIALIZATION =====
function init() {
    // Check for existing session
    authToken = localStorage.getItem('authToken');
    if (authToken) {
        verifyAndLoadUser();
    } else {
        showGuestMode();
    }

    // Event listeners
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('user-input').addEventListener('input', handleInputChange);
    document.getElementById('user-input').addEventListener('keydown', handleKeyPress);
    document.getElementById('attach-btn').addEventListener('click', () => document.getElementById('file-input').click());
    document.getElementById('file-input').addEventListener('change', handleFileSelect);
    document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);

    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => switchView(item.dataset.view));
    });

    // Detailed analysis toggle
    const detailedToggle = document.getElementById('detailed-analysis-toggle');
    detailedToggle.checked = localStorage.getItem('detailedAnalysis') === 'true';
    detailedToggle.addEventListener('change', (e) => {
        localStorage.setItem('detailedAnalysis', e.target.checked);
    });
}

// ===== AUTHENTICATION =====

async function verifyAndLoadUser() {
    try {
        const response = await fetch(`${API_BASE}/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            showAuthenticatedMode();
            loadChats();
        } else {
            // Token invalid
            handleLogout();
        }
    } catch (error) {
        console.error('Failed to verify user:', error);
        handleLogout();
    }
}

function showAuthenticatedMode() {
    document.getElementById('login-btn').style.display = 'none';
    document.getElementById('user-profile').style.display = 'flex';
    document.getElementById('new-chat-btn').style.display = 'flex';
    document.getElementById('chat-history').style.display = 'block';
    document.getElementById('sidebar-username').textContent = currentUser.username;
    document.getElementById('profile-username').textContent = currentUser.username;
    document.getElementById('profile-email').textContent = currentUser.email;
}

function showGuestMode() {
    document.getElementById('login-btn').style.display = 'flex';
    document.getElementById('user-profile').style.display = 'none';
    document.getElementById('new-chat-btn').style.display = 'none';
    document.getElementById('chat-history').style.display = 'none';
}

async function handleLogin(event) {
    event.preventDefault();

    const btn = event.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Signing in...';

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            closeAuthModal();
            showAuthenticatedMode();
            loadChats();
            showNotification('Welcome back, ' + currentUser.username + '!', 'success');
        } else {
            showNotification(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Connection error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function handleSignup(event) {
    event.preventDefault();

    const btn = event.target.querySelector('button');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Creating account...';

    const username = document.getElementById('signup-username').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            localStorage.setItem('authToken', authToken);
            closeAuthModal();
            showAuthenticatedMode();
            showNotification('Account created successfully!', 'success');
        } else {
            showNotification(data.detail || 'Signup failed', 'error');
        }
    } catch (error) {
        showNotification('Connection error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    currentChatId = null;
    localStorage.removeItem('authToken');
    showGuestMode();
    clearChat();
    closeSettings();
    showNotification('Logged out successfully', 'success');
}

// ===== MODAL CONTROLS =====

function openLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

function openSignupModal() {
    document.getElementById('signup-modal').classList.add('active');
}

function closeAuthModal() {
    document.getElementById('login-modal').classList.remove('active');
    document.getElementById('signup-modal').classList.remove('active');
}

function switchToSignup() {
    closeAuthModal();
    openSignupModal();
}

function switchToLogin() {
    closeAuthModal();
    openLoginModal();
}

function openSettings() {
    document.getElementById('settings-modal').classList.add('active');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

// ===== CHAT MANAGEMENT =====

async function loadChats() {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE}/chats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderChatList(data.chats);
        }
    } catch (error) {
        console.error('Failed to load chats:', error);
    }
}

function renderChatList(chats) {
    const chatList = document.getElementById('chat-list');
    chatList.innerHTML = '';

    if (chats.length === 0) {
        chatList.innerHTML = '<p class="no-chats">No chats yet. Start a new conversation!</p>';
        return;
    }

    chats.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item' + (chat.id === currentChatId ? ' active' : '');
        chatItem.innerHTML = `
            <div class="chat-item-content" onclick="loadChat(${chat.id})">
                <h4>${chat.title || 'New Chat'}</h4>
                <p>${new Date(chat.created_at).toLocaleDateString()}</p>
            </div>
            <button class="delete-chat-btn" onclick="deleteChat(${chat.id}, event)">
                <i class="fa-solid fa-trash"></i>
            </button>
        `;
        chatList.appendChild(chatItem);
    });
}

async function createNewChat() {
    if (!authToken) {
        openLoginModal();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/new_chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: 'New Chat' })
        });

        if (response.ok) {
            const data = await response.json();
            currentChatId = data.chat_id;
            clearChat();
            loadChats();
            showNotification('New chat created', 'success');
        }
    } catch (error) {
        showNotification('Failed to create chat', 'error');
    }
}

async function loadChat(chatId) {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE}/chats/${chatId}/messages`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            currentChatId = chatId;
            clearChat();
            data.messages.forEach(msg => {
                if (msg.sender === 'user') {
                    addUserMessage(msg.content);
                } else {
                    if (msg.analysis_data) {
                        addBotResponseWithTypewriter(msg.analysis_data);
                    } else {
                        addBotMessage(msg.content);
                    }
                }
            });
            loadChats(); // Refresh to update active state
        }
    } catch (error) {
        showNotification('Failed to load chat', 'error');
    }
}

async function deleteChat(chatId, event) {
    event.stopPropagation();

    if (!confirm('Delete this chat?')) return;

    try {
        const response = await fetch(`${API_BASE}/chats/${chatId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            if (currentChatId === chatId) {
                currentChatId = null;
                clearChat();
            }
            loadChats();
            showNotification('Chat deleted', 'success');
        }
    } catch (error) {
        showNotification('Failed to delete chat', 'error');
    }
}

function clearChat() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    document.getElementById('hero-section').style.display = 'flex';
}

// ===== MESSAGE HANDLING =====

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();

    if (!message) return;

    // Check authentication
    if (!authToken) {
        openLoginModal();
        return;
    }

    // Hide hero
    document.getElementById('hero-section').style.display = 'none';

    // Add user message
    addUserMessage(message);
    input.value = '';
    handleInputChange();

    // Show loading
    const loadingId = addLoading();

    try {
        const response = await fetch(`${API_BASE}/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId
            })
        });

        const data = await response.json();
        removeLoading(loadingId);

        if (response.ok) {
            // Update current chat ID if new chat was created
            if (data.chat_id) {
                currentChatId = data.chat_id;
                loadChats(); // Refresh chat list
            }
            addBotResponseWithTypewriter(data);
        } else {
            addBotMessage('Error: ' + (data.error || 'Analysis failed'));
        }
    } catch (error) {
        removeLoading(loadingId);
        addBotMessage('Connection error. Please check your internet connection.');
    }
}

function addUserMessage(text) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fa-solid fa-user"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = text.replace(/\n/g, '<br>');

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(text) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = text.replace(/\n/g, '<br>');

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addLoading() {
    const id = 'loading-' + Date.now();
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = id;

    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="message-bubble">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            Analyzing...
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    return id;
}

function removeLoading(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

async function addBotResponseWithTypewriter(data) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    const decision = data.decision || data;
    const extraction = data.extraction || {};
    const research = data.research || {};

    const category = decision.result || "Needs Verification";
    const summary = decision.summary || "";
    const explanation = decision.explanation || "";
    const redFlags = decision.red_flags || extraction.red_flags || [];

    let categoryClass = 'category-verification';
    let categoryIcon = '🟧';

    if (category === "Looks Safe") {
        categoryClass = 'category-safe';
        categoryIcon = '🟩';
    } else if (category === "Contains Warning Signs") {
        categoryClass = 'category-warning';
        categoryIcon = '🟥';
    }

    let responseHTML = `
        <div class="message-avatar">
            <i class="fa-solid fa-robot"></i>
        </div>
        <div class="message-bubble">
            <div class="result-card">
                <div class="category-badge ${categoryClass}">
                    <span class="category-icon">${categoryIcon}</span>
                    <span>${category}</span>
                </div>
                
                <div class="result-summary">
                    <strong>${summary || category}</strong>
                </div>
                
                <div class="result-explanation">
                    ${explanation.replace(/\n/g, '<br>')}
                </div>
    `;

    // Add detailed analysis if enabled
    const showDetailed = localStorage.getItem('detailedAnalysis') === 'true';
    if (showDetailed && (extraction.company_name || extraction.emails || extraction.fees || redFlags.length > 0)) {
        responseHTML += `
            <div class="analysis-breakdown">
                <div class="breakdown-header" onclick="toggleBreakdown(this)">
                    <i class="fa-solid fa-chevron-down"></i>
                    <span>Analysis Details</span>
                </div>
                <div class="breakdown-content" style="display: none;">
        `;

        if (extraction.company_name && extraction.company_name !== "Unknown") {
            responseHTML += `
                <div class="breakdown-item">
                    <strong>🏢 Company:</strong> ${extraction.company_name}
                </div>
            `;
        }

        if (extraction.emails && extraction.emails.length > 0) {
            responseHTML += `
                <div class="breakdown-item">
                    <strong>📧 Emails:</strong> ${extraction.emails.join(', ')}
                </div>
            `;
        }

        if (extraction.fees && extraction.fees.length > 0) {
            const feeList = extraction.fees.map(f => `₹${f.amount} (${f.type})`).join(', ');
            responseHTML += `
                <div class="breakdown-item">
                    <strong>💰 Fees Mentioned:</strong> ${feeList}
                </div>
            `;
        }

        if (redFlags.length > 0) {
            responseHTML += `
                <div class="breakdown-item">
                    <strong>⚠️ Red Flags:</strong>
                    <ul class="flag-list">
                        ${redFlags.slice(0, 5).map(flag => `<li>${flag}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (research.trust_assessment) {
            const trustEmoji = {
                'high_trust': '✅',
                'moderate_trust': '👍',
                'low_trust': '⚠️',
                'high_risk': '🚨'
            }[research.trust_assessment] || '❓';

            responseHTML += `
                <div class="breakdown-item">
                    <strong>${trustEmoji} Trust Level:</strong> ${research.trust_assessment.replace('_', ' ')}
                </div>
            `;
        }

        responseHTML += `
                </div>
            </div>
        `;
    }

    responseHTML += `
            </div>
        </div>
    `;

    messageDiv.innerHTML = responseHTML;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

window.toggleBreakdown = function (header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('i');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'fa-solid fa-chevron-up';
    } else {
        content.style.display = 'none';
        icon.className = 'fa-solid fa-chevron-down';
    }
};

// ===== UI HELPERS =====

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

function handleInputChange() {
    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    sendBtn.disabled = !input.value.trim();
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    const preview = document.getElementById('file-preview');
    preview.innerHTML = '';

    files.forEach(file => {
        const fileTag = document.createElement('div');
        fileTag.className = 'file-tag';
        fileTag.innerHTML = `
            <i class="fa-solid fa-file"></i>
            <span>${file.name}</span>
            <button onclick="removeFile(this)">×</button>
        `;
        preview.appendChild(fileTag);
    });
}

function removeFile(button) {
    button.parentElement.remove();
    if (document.getElementById('file-preview').children.length === 0) {
        document.getElementById('file-input').value = '';
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

function switchView(view) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');

    if (view === 'chat') {
        document.getElementById('chat-view').style.display = 'flex';
        document.getElementById('about-view').style.display = 'none';
    } else if (view === 'about') {
        document.getElementById('chat-view').style.display = 'none';
        document.getElementById('about-view').style.display = 'block';
    }
}

function useSuggestion(text) {
    document.getElementById('user-input').value = text;
    handleInputChange();
}

function showNotification(message, type = 'success') {
    const toast = document.getElementById('notification-toast');
    const messageSpan = document.getElementById('notification-message');

    messageSpan.textContent = message;
    toast.className = 'notification-toast ' + type;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ===== INITIALIZE =====
init();
