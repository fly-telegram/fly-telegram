import { handleLogin } from './auth.js';

const loginButton = document.querySelector('#login-button');
const formContainer = document.querySelector('.form-container');
const form = document.querySelector('form');

function animateButtonAndShowForm(event) {
  event.preventDefault();
  loginButton.classList.add('animate');
  setTimeout(() => {
    formContainer.classList.add('show');
    changeButtonText('LOGIN');
    loginButton.removeEventListener('click', animateButtonAndShowForm);
  }, 500);
}

function changeButtonText(text) {
  const textArray = text.split('');
  let i = 0;
  const interval = setInterval(() => {
    if (i < textArray.length) {
      loginButton.textContent = textArray.slice(0, i + 1).join('');
      i++;
    } else {
      clearInterval(interval);
    }
  }, 100);
}

loginButton.addEventListener('click', animateButtonAndShowForm);
form.addEventListener('submit', handleLogin);