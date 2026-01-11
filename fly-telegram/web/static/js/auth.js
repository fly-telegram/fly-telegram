import { showNotification } from './notifications.js';

const apiHashInput = document.querySelector('#api-hash');
const apiIdInput = document.querySelector('#api-id');
const phoneNumberInput = document.querySelector('#phone-number');
const popupContainer = document.querySelector('#popup-container');
const loginInput = document.querySelector('#login-input');
const twoFaPopup = document.getElementById('twofa-popup'); 
const twoFaPasswordInput = document.getElementById('twofa-password');
const twoFaSubmitButton = document.getElementById('twofa-submit');

export async function handleLogin(event) {
  event.preventDefault();
  console.log("ok");

  if (!validateInputs()) {
    showNotification('Please fill in all fields correctly.');
    return;
  }

  const apiHash = apiHashInput.value.trim();
  const apiId = apiIdInput.value.trim();
  const phoneNumber = phoneNumberInput.value.trim();

  try {
    showNotification('Sending code... Please wait');
    const response = await sendRequest('/send_code', { phone: phoneNumber });

    if (!response.ok) {
      const errorData = await response.json();
      showNotification(errorData.detail || 'Failed to send code');
      return;
    }

    const data = await response.json();
    showPopup(data.code_hash);
  } catch (error) {
    showNotification('Failed to send code');
  }
}

function showPopup(codeHash) {
  popupContainer.style.display = 'flex';
  loginInput.setAttribute('data-code-hash', codeHash);
}

function validateInputs() {
  const apiHash = apiHashInput.value.trim();
  const apiId = apiIdInput.value.trim();
  const phoneNumber = phoneNumberInput.value.trim();

  if (!apiHash || !apiId || !phoneNumber) {
    showNotification('Please fill in all fields.');
    return false;
  }

  if (isNaN(apiId)) {
    showNotification('API ID must be a number.');
    return false;
  }

  if (isNaN(phoneNumber)) {
    showNotification('Phone number must be a number.');
    return false;
  }

  return true;
}

async function handleConfirmationCodeInput(event) {
  if (event.key === 'Enter') {
    const code = loginInput.value.trim();
    const codeHash = loginInput.getAttribute('data-code-hash');
    const phoneNumber = phoneNumberInput.value.trim();

    if (!code || !codeHash) {
      showNotification('Please enter a valid confirmation code.');
      return;
    }

    try {
      const response = await sendRequest('/sign_in', { phone: phoneNumber, code_hash: codeHash, code: code });

      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.status === '2fa_required') {
          showtwofaPopup();
        } else {
          showNotification(errorData.detail || 'Failed to sign in');
        }
        return;
      }

      const data = await response.json();
      showNotification(`Welcome, ${data.user}!`);
      popupContainer.style.display = 'none';
    } catch (error) {
      showNotification('Failed to sign in');
    }
  }
}

function showtwofaPopup() {
  twoFaPopup.style.display = 'block';
  twoFaSubmitButton.addEventListener('click', handletwofaSubmit);
}

async function handletwofaSubmit() {
  const password = twoFaPasswordInput.value.trim();
  const phoneNumber = phoneNumberInput.value.trim();

  if (!password) {
    showNotification('Please enter your 2fa password.');
    return;
  }

  try {
    const response = await sendRequest('/sign_in', { phone: phoneNumber, password: password });

    if (!response.ok) {
      const errorData = await response.json();
      showNotification(errorData.detail || 'Failed to sign in');
      return;
    }

    const data = await response.json();
    showNotification(`Welcome, ${data.user}!`);
    popupContainer.style.display = 'none';
  } catch (error) {
    showNotification('Failed to sign in');
  }
}

async function sendRequest(url, body) {
  return await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams(body),
  });
}
