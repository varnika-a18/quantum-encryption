/**
 * WEEK 3: INTEGRATION LEAD & ERROR HANDLING CODE (Person 5)
 * Handles network status checks, error catch blocks, and CORS/connection debugging.
 */

const BACKEND_URL = window.location.origin.includes('localhost') 
    ? 'http://127.0.0.1:5000' 
    : window.location.origin;

// --- 1. NETWORK & CONNECTION DEBUGGER ---
async function debugBackendConnection() {
    console.log("🔄 Person 5 Integration Check: Pinging backend server at:", BACKEND_URL);
    try {
        const response = await fetch(`${BACKEND_URL}/api/signup`, { 
            method: 'OPTIONS' 
        });
        console.log("✅ Connection Test Success! Status:", response.status);
        return true;
    } catch (error) {
        console.error("❌ ERROR: Connection to server failed!");
        showSystemOfflineBanner();
        return false;
    }
}

// --- 2. EDGE CASE HANDLE: SYSTEM OFFLINE ---
function showSystemOfflineBanner() {
    let offlineBanner = document.getElementById('network-error-banner');
    if (!offlineBanner) {
        offlineBanner = document.createElement('div');
        offlineBanner.id = 'network-error-banner';
        offlineBanner.style = "background-color: #ff9800; color: white; text-align: center; padding: 10px; position: fixed; top: 0; width: 100%; z-index: 9999; font-weight: bold;";
        offlineBanner.textContent = "⚠️ Connection Issue: Lost connection to the secure chat server. Retrying...";
        document.body.prepend(offlineBanner);
    }
}

// --- 3. EDGE CASE HANDLE: QUANTUM KEY GENERATION FAILURE ---
function handleQuantumFailureGracefully(apiErrorData) {
    console.warn("⚠️ Edge Case Handled: Quantum Key Negotiation Stopped.", apiErrorData);
    const quantumStatus = document.getElementById('quantum-status');
    const chatMessages = document.getElementById('chat-messages');

    if (quantumStatus) {
        quantumStatus.textContent = "Status: CRITICAL SECURE FAILURE - KEY ABORTED";
        quantumStatus.style.color = "purple";
    }

    if (chatMessages) {
        const systemNotice = document.createElement('div');
        systemNotice.className = "system-warning-bubble";
        systemNotice.style = "background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; padding: 8px; margin: 10px 0; border-radius: 5px; text-align: center; font-size: 0.9em;";
        systemNotice.textContent = "🔒 System Notice: Encryption key aborted due to excessive channel noise/eavesdropping. Transmission paused for your safety.";
        chatMessages.appendChild(systemNotice);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    debugBackendConnection();
});