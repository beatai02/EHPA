/**
 * EHPA Chat JavaScript
 * Chatbot functionality and message handling
 */

// Chat state
let chatHistory = [];

// Initialize chat
document.addEventListener('DOMContentLoaded', () => {
    setupChatInput();
});

// Setup chat input
function setupChatInput() {
    const chatInput = document.getElementById('chatInput');

    if (!chatInput) return;

    // Send on Enter
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

// Send message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to UI
    addChatMessage('user', message);

    // Clear input
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        // Send via WebSocket if available
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'chat',
                message: message
            }));
        } else {
            // Fallback to HTTP
            const response = await window.dashboard.apiRequest('/api/v1/chat/message', {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    session_id: currentSession?.session_id || 'default'
                })
            });

            removeTypingIndicator();
            addChatMessage('bot', response.response || response.message);

            // Handle suggestions
            if (response.suggestions) {
                addSuggestions(response.suggestions);
            }
        }

        // Add to history
        chatHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date()
        });

    } catch (error) {
        console.error('Failed to send message:', error);
        removeTypingIndicator();
        addChatMessage('bot', 'Sorry, I encountered an error. Please try again.');
    }
}

// Add chat message to UI
function addChatMessage(role, content) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user'
        ? '<i class="fas fa-user"></i>'
        : '<i class="fas fa-robot"></i>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    // Process content (handle markdown-like formatting)
    messageContent.innerHTML = formatMessageContent(content);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Add to history
    chatHistory.push({
        role,
        content,
        timestamp: new Date()
    });
}

// Format message content
function formatMessageContent(content) {
    // Convert newlines to <br>
    let formatted = content.replace(/\n/g, '<br>');

    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Convert `code` to <code>
    formatted = formatted.replace(/`(.*?)`/g, '<code style="background: var(--bg-darker); padding: 2px 6px; border-radius: 3px;">$1</code>');

    // Convert URLs to links
    formatted = formatted.replace(
        /(https?:\/\/[^\s]+)/g,
        '<a href="$1" target="_blank" style="color: var(--primary-color);">$1</a>'
    );

    // Convert bullet points
    formatted = formatted.replace(/^- (.+)/gm, '<li>$1</li>');
    if (formatted.includes('<li>')) {
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }

    // Convert numbered lists
    formatted = formatted.replace(/^\d+\. (.+)/gm, '<li>$1</li>');

    return formatted;
}

// Show typing indicator
function showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const typing = document.createElement('div');
    typing.className = 'message bot typing-indicator';
    typing.id = 'typingIndicator';
    typing.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typing = document.getElementById('typingIndicator');
    if (typing) {
        typing.remove();
    }
}

// Add suggestions
function addSuggestions(suggestions) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages || !suggestions || suggestions.length === 0) return;

    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'chat-suggestions';
    suggestionsDiv.style.cssText = 'display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;';

    suggestions.forEach(suggestion => {
        const btn = document.createElement('button');
        btn.className = 'suggestion-btn';
        btn.style.cssText = 'padding: 0.5rem 1rem; background: var(--bg-darker); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-primary); cursor: pointer; transition: all 0.3s;';
        btn.textContent = suggestion;
        btn.onclick = () => {
            document.getElementById('chatInput').value = suggestion;
            sendMessage();
        };
        suggestionsDiv.appendChild(btn);
    });

    const lastMessage = chatMessages.lastElementChild;
    if (lastMessage && lastMessage.classList.contains('bot')) {
        lastMessage.querySelector('.message-content').appendChild(suggestionsDiv);
    }
}

// Predefined quick actions
function sendQuickAction(action) {
    document.getElementById('chatInput').value = action;
    sendMessage();
}

// Clear chat history
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    chatMessages.innerHTML = `
        <div class="message bot">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>Chat cleared. How can I help you?</p>
            </div>
        </div>
    `;

    chatHistory = [];
}

// Export chat history
function exportChatHistory() {
    const blob = new Blob([JSON.stringify(chatHistory, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ehpa-chat-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Add CSS for typing indicator
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: flex;
        gap: 4px;
        padding: 8px 0;
    }

    .typing-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-secondary);
        animation: typing 1.4s infinite;
    }

    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }

    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0.3;
            transform: translateY(0);
        }
        30% {
            opacity: 1;
            transform: translateY(-10px);
        }
    }

    .suggestion-btn:hover {
        background: var(--bg-hover) !important;
        border-color: var(--primary-color) !important;
    }
`;
document.head.appendChild(style);

// Make functions available globally
window.sendMessage = sendMessage;
window.addChatMessage = addChatMessage;
window.sendQuickAction = sendQuickAction;
window.clearChat = clearChat;
window.exportChatHistory = exportChatHistory;
