document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const typingIndicator = document.getElementById("typing-indicator");

    // Handle the form submission
    document.getElementById("chat-form").addEventListener("submit", handleSubmit);

    function handleSubmit(event) {
        event.preventDefault();
        const messageInput = document.getElementById("user-message");
        const message = messageInput.value.trim();
        if (!message) return;
        sendMessage(message);
        messageInput.value = "";
    }

    // Send a message to the Flask backend
    window.sendMessage = function(message) {
        appendMessage(message, "user");
        showTypingIndicator(true);

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        })
        .then(response => response.json())
        .then(data => {
            showTypingIndicator(false);
            appendMessage(data.reply, "assistant");
        })
        .catch((error) => {
            console.error("Error:", error);
            showTypingIndicator(false);
        });
    };

    // Continue chat
    window.continueChat = function() {
        sendMessage("continue");
    };

    // Reset chat
    window.resetChat = function() {
        fetch("/reset", { method: "POST" })
            .then(() => {
                chatBox.innerHTML = "";
            });
    };

    // Append a message to the chat box
    function appendMessage(message, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.classList.add("chat-message", sender);

        if (sender === "assistant") {
            // Use the Ottoman AI avatar
            msgDiv.innerHTML = `
                <img src="/static/images/ottoman-ai.png" alt="Ottoman AI" class="chat-avatar" />
                <div class="message-text">${message}</div>
            `;
        } else {
            msgDiv.innerHTML = `<p>${message}</p>`;
        }

        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Show or hide the typing indicator
    function showTypingIndicator(show) {
        if (show) {
            typingIndicator.classList.remove("hidden");
            typingIndicator.classList.add("visible");
        } else {
            typingIndicator.classList.remove("visible");
            typingIndicator.classList.add("hidden");
        }
    }
});
