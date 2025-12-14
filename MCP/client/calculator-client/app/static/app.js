let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 2000;

let currentAssistantMessage = null;
let isProcessing = false;

const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        updateStatus('connected');
        enableInput();
    };

    ws.onmessage = (event) => {
        const message = event.data;

        if (message === '[DONE]') {
            currentAssistantMessage = null;
            isProcessing = false;
            enableInput();
            scrollToBottom();
            return;
        }

        if (!currentAssistantMessage) {
            currentAssistantMessage = createAssistantMessage();
        }

        appendToAssistantMessage(message);
        scrollToBottom();
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateStatus('disconnected');
        disableInput();

        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            updateStatus(`reconnecting (${reconnectAttempts}/${maxReconnectAttempts})`);
            setTimeout(connectWebSocket, reconnectDelay * reconnectAttempts);
        } else {
            updateStatus('connection failed');
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error');
    };
}

function createUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    return messageDiv;
}

function createAssistantMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    return contentDiv;
}

function appendToAssistantMessage(text) {
    if (currentAssistantMessage) {
        currentAssistantMessage.textContent += text;
    }
}

function sendMessage() {
    const message = userInput.value.trim();

    if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing) {
        return;
    }

    createUserMessage(message);
    userInput.value = '';

    isProcessing = true;
    disableInput();

    ws.send(message);

    scrollToBottom();
}

function updateStatus(status) {
    const statusMap = {
        'connected': { text: 'Connected', class: 'connected' },
        'disconnected': { text: 'Disconnected', class: 'disconnected' },
        'error': { text: 'Error', class: 'error' },
        'connection failed': { text: 'Connection Failed', class: 'error' }
    };

    if (status.startsWith('reconnecting')) {
        statusDot.className = 'status-dot reconnecting';
        statusText.textContent = `Reconnecting ${status.match(/\(.*\)/)?.[0] || ''}`;
    } else {
        const statusInfo = statusMap[status] || { text: status, class: 'disconnected' };
        statusDot.className = `status-dot ${statusInfo.class}`;
        statusText.textContent = statusInfo.text;
    }
}

function enableInput() {
    if (!isProcessing) {
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
}

function disableInput() {
    userInput.disabled = true;
    sendButton.disabled = true;
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

connectWebSocket();

window.addEventListener('beforeunload', () => {
    if (ws) {
        ws.close();
    }
});
