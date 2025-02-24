document.addEventListener("DOMContentLoaded", function () {
    const darkModeToggle = document.getElementById("dark-mode-toggle");
    const typingIndicator = document.getElementById("typing-indicator");

    if (localStorage.getItem("dark-mode") === "enabled") {
        document.body.classList.add("dark-mode");
    }

    darkModeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        localStorage.setItem("dark-mode", document.body.classList.contains("dark-mode") ? "enabled" : "disabled");
    });

    document.getElementById("reset-btn").addEventListener("click", resetChat);
    document.getElementById("continue-btn").addEventListener("click", () => sendMessage("continue"));
});

function handleSubmit(event) {
    event.preventDefault();
    const messageInput = document.getElementById("user-message");
    sendMessage(messageInput.value.trim());
    messageInput.value = "";  // Clear input after sending
}

function resetChat() {
    fetch("/reset", { method: "POST" })
        .then(response => response.json())
        .then(data => {
            document.getElementById("chat-box").innerHTML = "";
            appendMessage(data.message, "assistant");
        });
}

function sendMessage(message) {
    if (!message) return;

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
        appendMessage(data.reply ?? "⚠️ No response from server.", "assistant");

        if (data.show_ad) {
            appendAd();
        }
    });
}

function appendMessage(message, sender) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.classList.add("chat-message", sender);
    messageElement.innerHTML = `<p>${message}</p>`;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showTypingIndicator(show) {
    const indicator = document.getElementById("typing-indicator");
    indicator.classList.toggle("visible", show);
}

function appendAd() {
    const chatBox = document.getElementById("chat-box");
    const adContainer = document.createElement("div");
    adContainer.classList.add("chat-message", "assistant");
    adContainer.innerHTML = `
        <ins class="adsbygoogle"
             style="display:block; text-align:center; margin-top:10px;"
             data-ad-client="ca-4928946447051580"
             data-ad-slot="3754304957"
             data-ad-format="fluid"
             data-full-width-responsive="true"></ins>
    `;
    chatBox.appendChild(adContainer);
    chatBox.scrollTop = chatBox.scrollHeight;
    (adsbygoogle = window.adsbygoogle || []).push({});
}
