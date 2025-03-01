// Initialize chat history
let chatMessages = [];

// Save chat history to localStorage
function saveChatHistory() {
    localStorage.setItem("chat_history", JSON.stringify(chatMessages));
}

// Load chat history from localStorage
function loadChatHistory() {
    let storedChat = localStorage.getItem("chat_history");
    if (storedChat) {
        chatMessages = JSON.parse(storedChat);
        renderChatHistory();
    }
}

// Function to render chat history
function renderChatHistory() {
    let chatContainer = document.getElementById("chat-container");
    chatContainer.innerHTML = ""; // Clear previous messages

    chatMessages.forEach((msg) => {
        let msgDiv = document.createElement("div");
        msgDiv.classList.add("message");

        if (msg.role === "user") {
            msgDiv.classList.add("user-message");
        } else if (msg.role === "assistant") {
            msgDiv.classList.add("assistant-message");
        }

        msgDiv.innerHTML = msg.content;
        chatContainer.appendChild(msgDiv);
    });

    chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll
}

// Load chat history on page load
window.onload = function() {
    loadChatHistory();
};

// Function to handle sending messages
function sendMessage() {
    let userInput = document.getElementById("user_input").value;

    if (userInput.trim() === "") return;

    // Add user message to chat history
    chatMessages.push({ role: "user", content: userInput });
    saveChatHistory();
    renderChatHistory();

    // Show "typing" indicator
    showTypingIndicator();

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        chatMessages.push({ role: "assistant", content: data.reply });
        saveChatHistory();
        renderChatHistory();
    })
    .catch(error => {
        hideTypingIndicator();
        console.error("Error:", error);
    });

    document.getElementById("user_input").value = ""; // Clear input field
}

// Function to show "Ottoman AI is typing..."
function showTypingIndicator() {
    let chatContainer = document.getElementById("chat-container");
    let typingDiv = document.createElement("div");
    typingDiv.classList.add("typing-indicator");
    typingDiv.id = "typing-indicator";
    typingDiv.innerHTML = "Ottoman AI is typing...";
    chatContainer.appendChild(typingDiv);
}

// Function to hide "typing" indicator
function hideTypingIndicator() {
    let typingIndicator = document.getElementById("typing-indicator");
    if (typingIndicator) typingIndicator.remove();
}

// Function to handle "Continue" button
function continueChat() {
    if (chatMessages.length > 0) {
        let lastMessage = chatMessages[chatMessages.length - 1].content;
        sendMessageWithContent("Continue from where you left off: " + lastMessage);
    }
}

// Send message with predefined content (for "Continue" button)
function sendMessageWithContent(message) {
    chatMessages.push({ role: "user", content: message });
    saveChatHistory();
    renderChatHistory();

    // Show "typing" indicator
    showTypingIndicator();

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        chatMessages.push({ role: "assistant", content: data.reply });
        saveChatHistory();
        renderChatHistory();
    })
    .catch(error => {
        hideTypingIndicator();
        console.error("Error:", error);
    });
}

// Function to reset chat
function resetChat() {
    chatMessages = [];
    localStorage.removeItem("chat_history");
    fetch("/reset", { method: "POST" })
    .then(() => {
        renderChatHistory();
    });
}

// Handle session transfer from parent page (for embedded iframe)
window.addEventListener("message", function(event) {
    if (event.origin === "https://your-parent-website.com") {
        document.cookie = event.data.sessionToken;
    }
}, false);

// Event listeners for buttons
document.getElementById("send_button").addEventListener("click", sendMessage);
document.getElementById("reset_button").addEventListener("click", resetChat);
document.getElementById("continue_button").addEventListener("click", continueChat);
