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
  if (event) {
    event.preventDefault();
  }
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
  loginInput.focus();
  loginInput.addEventListener('keypress', handleConfirmationCodeInput);
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
      const response = await sendRequest('/sign_in', { 
        phone: phoneNumber, 
        code_hash: codeHash, 
        code: code 
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (errorData.status === '2fa_required') {
          showTwoFaPopup();
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

function showTwoFaPopup() {
  twoFaPopup.style.display = 'block';
  twoFaPasswordInput.focus();

  twoFaSubmitButton.removeEventListener('click', handleTwoFaSubmit);
  twoFaSubmitButton.addEventListener('click', handleTwoFaSubmit);
}

async function handleTwoFaSubmit() {
  const password = twoFaPasswordInput.value.trim();
  const phoneNumber = phoneNumberInput.value.trim();

  const code = loginInput.value.trim()
  const code_hash = loginInput.getAttribute('data-code-hash')

  if (!password) {
    showNotification('Please enter your 2FA password.');
    return;
  }

  try {
    const response = await sendRequest('/sign_in', { 
      phone: phoneNumber, 
      password: password,
      code: code,
      code_hash: code_hash
    });

    if (!response.ok) {
      const err = await response.json();
      const message = err.detail;
      showNotification(typeof msg == 'string' ? msg : JSON.stringify(msg));
      return;
    }

    const data = await response.json();
    showNotification(`Welcome, ${data.user}!`);
    popupContainer.style.display = 'none';
  } catch (error) {
    showNotification(error.message || 'Failed to sign in');
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

const codePopup = document.getElementById('code-popup');
if (codePopup) {
  codePopup.addEventListener('submit', function(event) {
    event.preventDefault();
    handleConfirmationCodeInput({ key: 'Enter' });
  });
}