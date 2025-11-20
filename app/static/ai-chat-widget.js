// AI Chat Widget - Floating assistant for Contractor Portal
// Place this script on any page to enable AI assistance

class AIChatWidget {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.apiBaseUrl = window.API_BASE_URL || '';
        this.currentPage = this.detectCurrentPage();
        this.init();
    }

    detectCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('WinterOpsLog')) return 'WinterOpsLog';
        if (path.includes('GreenOpsLog')) return 'GreenOpsLog';
        if (path.includes('MyTickets')) return 'MyTickets';
        if (path.includes('PropertyInfo')) return 'PropertyInfo';
        return 'default';
    }

    init() {
        this.injectStyles();
        this.createWidget();
        this.loadSuggestions();
    }

    injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .ai-chat-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                z-index: 10000;
                transition: transform 0.2s;
            }

            .ai-chat-button:hover {
                transform: scale(1.1);
            }

            .ai-chat-window {
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 450px;
                height: 550px;
                background: #1a1a1a;
                border: 2px solid #667eea;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.4);
                display: none;
                flex-direction: column;
                z-index: 10000;
                font-family: 'Courier New', monospace;
            }

            .ai-chat-window.open {
                display: flex;
            }

            .ai-chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .ai-chat-header h3 {
                margin: 0;
                font-size: 16px;
            }

            .ai-chat-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
            }

            .ai-chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: #0a0a0a;
            }

            .ai-message {
                margin-bottom: 15px;
                padding: 10px;
                border-radius: 8px;
                max-width: 85%;
                word-wrap: break-word;
            }

            .ai-message.user {
                background: #003300;
                color: #80ff80;
                border: 1px solid #80ff80;
                margin-left: auto;
                text-align: right;
            }

            .ai-message.assistant {
                background: #1a1a2e;
                color: #a0a0ff;
                border: 1px solid #667eea;
            }

            .ai-message.system {
                background: #1a1a1a;
                color: #888;
                border: 1px solid #333;
                text-align: center;
                font-size: 12px;
                max-width: 100%;
            }

            .ai-suggestions {
                padding: 10px 15px;
                background: #0a0a0a;
                border-top: 1px solid #333;
                display: flex;
                flex-wrap: wrap;
                gap: 5px;
            }

            .ai-suggestions.hidden {
                display: none;
            }

            .ai-suggestion-btn {
                background: #1a1a2e;
                color: #667eea;
                border: 1px solid #667eea;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            }

            .ai-suggestion-btn:hover {
                background: #667eea;
                color: white;
            }

            .ai-chat-input-container {
                padding: 15px;
                background: #0a0a0a;
                border-top: 1px solid #333;
                display: flex;
                gap: 10px;
            }

            .ai-chat-input {
                flex: 1;
                background: #1a1a1a;
                color: #80ff80;
                border: 1px solid #80ff80;
                padding: 10px;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }

            .ai-chat-send {
                background: #003300;
                color: #80ff80;
                border: 1px solid #80ff80;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-family: 'Courier New', monospace;
                transition: all 0.2s;
            }

            .ai-chat-send:hover {
                background: #004400;
            }

            .ai-chat-send:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .ai-typing {
                color: #667eea;
                font-style: italic;
                font-size: 12px;
                padding: 10px;
            }

            @media (max-width: 768px) {
                .ai-chat-window {
                    width: calc(100vw - 40px);
                    height: 500px;
                    right: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    createWidget() {
        // Chat button
        const button = document.createElement('button');
        button.className = 'ai-chat-button';
        button.innerHTML = '🤖';
        button.setAttribute('aria-label', 'Open AI Assistant');
        button.onclick = () => this.toggle();
        document.body.appendChild(button);
        this.button = button;

        // Chat window
        const window = document.createElement('div');
        window.className = 'ai-chat-window';
        window.innerHTML = `
            <div class="ai-chat-header">
                <h3>🤖 AI Assistant</h3>
                <button class="ai-chat-close" aria-label="Close">×</button>
            </div>
            <div class="ai-chat-messages" id="ai-messages"></div>
            <div class="ai-suggestions" id="ai-suggestions"></div>
            <div class="ai-chat-input-container">
                <input type="text" class="ai-chat-input" id="ai-input" placeholder="Ask me anything..." />
                <button class="ai-chat-send" id="ai-send">Send</button>
            </div>
        `;
        document.body.appendChild(window);
        this.window = window;

        // Event listeners
        window.querySelector('.ai-chat-close').onclick = () => this.close();
        window.querySelector('#ai-send').onclick = () => this.sendMessage();
        window.querySelector('#ai-input').onkeypress = (e) => {
            if (e.key === 'Enter') this.sendMessage();
        };

        // Welcome message
        this.addMessage('system', '👋 Hi! I\'m your AI assistant. How can I help you today?');
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.window.classList.add('open');
        this.window.querySelector('#ai-input').focus();
    }

    close() {
        this.isOpen = false;
        this.window.classList.remove('open');
    }

    addMessage(role, content) {
        const messagesDiv = this.window.querySelector('#ai-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${role}`;
        messageDiv.textContent = content;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        if (role !== 'system') {
            this.messages.push({ role, content });
        }
    }

    showTyping() {
        const messagesDiv = this.window.querySelector('#ai-messages');
        const typing = document.createElement('div');
        typing.className = 'ai-typing';
        typing.id = 'ai-typing';
        typing.textContent = 'AI is thinking...';
        messagesDiv.appendChild(typing);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    hideTyping() {
        const typing = this.window.querySelector('#ai-typing');
        if (typing) typing.remove();
    }

    async sendMessage() {
        const input = this.window.querySelector('#ai-input');
        const sendBtn = this.window.querySelector('#ai-send');
        const message = input.value.trim();

        if (!message) return;

        // Hide suggestions after first question
        const suggestionsDiv = this.window.querySelector('#ai-suggestions');
        if (suggestionsDiv) {
            suggestionsDiv.classList.add('hidden');
        }

        // Add user message
        this.addMessage('user', message);
        input.value = '';
        sendBtn.disabled = true;

        // Show typing indicator
        this.showTyping();

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(`${this.apiBaseUrl}/ai/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    messages: this.messages,
                    page_context: this.currentPage
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'AI request failed');
            }

            const data = await response.json();
            this.hideTyping();
            this.addMessage('assistant', data.message);

        } catch (error) {
            this.hideTyping();
            console.error('AI chat error:', error);
            this.addMessage('system', `❌ Error: ${error.message}`);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async loadSuggestions() {
        try {
            const token = localStorage.getItem('token');
            if (!token) return;

            const response = await fetch(`${this.apiBaseUrl}/ai/suggestions/?page=${this.currentPage}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) return;

            const data = await response.json();
            const suggestionsDiv = this.window.querySelector('#ai-suggestions');

            data.suggestions.forEach(suggestion => {
                const btn = document.createElement('button');
                btn.className = 'ai-suggestion-btn';
                btn.textContent = suggestion;
                btn.onclick = () => {
                    this.window.querySelector('#ai-input').value = suggestion;
                    this.sendMessage();
                };
                suggestionsDiv.appendChild(btn);
            });

        } catch (error) {
            console.error('Failed to load suggestions:', error);
        }
    }
}

// Initialize widget when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiChatWidget = new AIChatWidget();
    });
} else {
    window.aiChatWidget = new AIChatWidget();
}
