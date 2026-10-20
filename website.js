// --- CONFIGURATION & SESSION STATE ---
const API_BASE_URL = window.location.origin + '/api'; 
const currentUser = localStorage.getItem('username') || "AnonymousUser";
const authToken = localStorage.getItem('token'); 

let activeRecipient = null; 
let quantumKeySecure = true;

// --- DOM ELEMENTS ---
// Chat Interface
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const chatMessagesContainer = document.getElementById('chat-messages');
const activeChatHeader = document.getElementById('active-chat-header');

// Quantum Dashboard Panel Elements
const eavesdropperToggle = document.getElementById('eavesdropper-toggle');
const quantumStatusIndicator = document.getElementById('quantum-status');
const quantumAlertBanner = document.getElementById('quantum-alert-banner');
const qberDisplay = document.getElementById('qber-value');
const keyLengthDisplay = document.getElementById('key-length');

// Quantum Stream Visualization Container (The Table/Grid body)
const quantumStreamVisualizer = document.getElementById('quantum-stream-data');


// --- 1. SET UP CONVERSATION ---
function setActiveChatPartner(strangerUsername) {
    activeRecipient = strangerUsername;
    if (activeChatHeader) activeChatHeader.textContent = `Chatting with: ${strangerUsername}`;
    chatMessagesContainer.innerHTML = '';
    
    // Automatically trigger a unique quantum key exchange for this stranger
    triggerQuantumKeyGeneration();
    fetchChatMessages();
}


// --- 2. ADVANCED QUANTUM DASHBOARD LOGIC (Person 5 Core) ---
async function triggerQuantumKeyGeneration() {
    if (!activeRecipient) return; 
    const isEvePresent = eavesdropperToggle.checked;
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate-key`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ 
                sender: currentUser,
                receiver: activeRecipient,
                eve_toggle: isEvePresent 
            })
        });

        const data = await response.json();
        // Expecting data structure from Person 1 containing: 
        // status, qber, final_key, and simulation_blocks [alice_bits, alice_bases, bob_bases, filtered]

        if (response.status === 403 || data.status === 'compromised' || data.alert) {
            quantumKeySecure = false;
            updateQuantumUI(false, data.qber, data.final_key);
        } else {
            quantumKeySecure = true;
            updateQuantumUI(true, data.qber, data.final_key);
        }

        // Render the granular photon data into your Quantum Dashboard UI panel
        if (data.simulation_blocks) {
            renderQuantumStreamTable(data.simulation_blocks);
        }

    } catch (error) {
        console.error("Quantum Key exchange failed to communicate:", error);
    }
}

// Dynamically builds the photon transmission logs
function renderQuantumStreamTable(blocks) {
    if (!quantumStreamVisualizer) return;
    quantumStreamVisualizer.innerHTML = ''; // Reset panel view

    // Loop through each photon bit transmitted in the BB84 simulation
    blocks.forEach((photon, index) => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>#${index + 1}</td>
            <td>${photon.alice_bit}</td>
            <td><strong>${photon.alice_basis}</strong></td>
            <td><strong>${photon.bob_basis}</strong></td>
            <td><span class="${photon.basis_match ? 'match-true' : 'match-false'}">${photon.basis_match ? '✅ Match' : '❌ Mismatch'}</span></td>
            <td>${photon.bob_measured_bit ?? '-'}</td>
            <td><code class="sifted-block">${photon.sifted_bit !== null ? photon.sifted_bit : '-'}</code></td>
        `;
        quantumStreamVisualizer.appendChild(row);
    });
}

function updateQuantumUI(isSecure, qberValue, finalKey) {
    const percentageQber = (qberValue * 100).toFixed(1);
    if (qberDisplay) qberDisplay.textContent = `${percentageQber}%`;
    if (keyLengthDisplay) keyLengthDisplay.textContent = finalKey ? `${finalKey.length} bits` : '0 bits';

    if (!isSecure) {
        quantumStatusIndicator.textContent = "Status: KEY ABORTED (Eavesdropper Intercepted)";
        quantumStatusIndicator.className = "status-danger";
        if (quantumAlertBanner) quantumAlertBanner.style.display = "block";
    } else {
        quantumStatusIndicator.textContent = "Status: QUANTUM CHANNEL SECURE";
        quantumStatusIndicator.className = "status-success";
        if (quantumAlertBanner) quantumAlertBanner.style.display = "none";
    }
}

eavesdropperToggle.addEventListener('change', triggerQuantumKeyGeneration);


// --- 3. CHAT COMPONENT UTILITIES ---
async function sendMessage() {
    const textMessage = messageInput.value.trim();
    if (!textMessage || !activeRecipient) return;

    try {
        const response = await fetch(`${API_BASE_URL}/send-message`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                sender: currentUser,
                recipient: activeRecipient,
                plaintext_message: textMessage,
                is_hacked_toggle: !quantumKeySecure // Informs backend if channel is insecure
            })
        });

        if (response.ok) {
            messageInput.value = ''; 
            fetchChatMessages();     
        }
    } catch (error) {
        console.error("Message send failure:", error);
    }
}

async function fetchChatMessages() {
    if (!activeRecipient) return;

    try {
        const response = await fetch(`${API_BASE_URL}/messages/${activeRecipient}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const messages = await response.json();

        chatMessagesContainer.innerHTML = '';

        messages.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message-bubble');
            messageDiv.classList.add(msg.sender === currentUser ? 'my-message' : 'stranger-message');
            
            // Text is readable if secure, automatically jumbled by Person 3's API if compromised
            messageDiv.textContent = msg.payload; 
            chatMessagesContainer.appendChild(messageDiv);
        });

        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight; 
    } catch (error) {
        console.error("Error drawing latest messages:", error);
    }
}

// --- INITIALIZATION KEY STROKES ---
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

setInterval(fetchChatMessages, 2500); // Poll message changes