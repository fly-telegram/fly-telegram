import {
    showNotification
} from './notifications.js';

const qrCodeArea = document.getElementById('qr-code-area');
const qrStatus = document.getElementById('qr-status');
let qrPollInterval = null;

export async function initQrLogin() {
    qrStatus.textContent = 'Initializing...';

    try {
        const response = await fetch('/qr_init', {
            method: 'POST',
        });

        if (!response.ok) {
            const err = await response.json();
            qrStatus.textContent = 'Failed to load QR';
            showNotification(err.detail || 'QR init failed');
            return;
        }

        const data = await response.json();

        if (data.status === 'already_logged_in') {
            qrStatus.textContent = `Already logged in as ${data.user}`;
            return;
        }

        qrCodeArea.innerHTML = data.qr_svg;
        qrStatus.textContent = 'Waiting for scan...';

        startPolling();
    } catch (error) {
        qrStatus.textContent = 'Connection error';
        showNotification('Failed to load QR login');
    }
}

function startPolling() {
    if (qrPollInterval) {
        clearInterval(qrPollInterval);
    }

    qrPollInterval = setInterval(async () => {
        try {
            const response = await fetch('/qr_poll', {
                method: 'POST',
            });

            const data = await response.json();

            if (data.status === 'success') {
                clearInterval(qrPollInterval);
                qrPollInterval = null;
                qrStatus.textContent = `Welcome, ${data.user}!`;
                showNotification(`Welcome, ${data.user}!`);
            }
        } catch (error) {
            qrStatus.textContent = 'Polling...';
        }
    }, 2000);
}

export function stopQrPolling() {
    if (qrPollInterval) {
        clearInterval(qrPollInterval);
        qrPollInterval = null;
    }
}