import { handleLogin } from './auth.js';

const loginButton = document.querySelector('#login-button');
const formContainer = document.querySelector('.form-container');
const loginForm = document.querySelector('#login-form');

let isSetupMode = true;

function animateButtonAndShowForm(event) {
    event.preventDefault();
    
    if (isSetupMode) {
        loginButton.classList.add('animate');
        setTimeout(() => {
            formContainer.classList.add('show');
            changeButtonText('LOGIN');
            isSetupMode = false;
        }, 500);
    } else {
        handleLogin(event);
    }
}

function changeButtonText(text) {
    loginButton.textContent = text;
}

loginButton.addEventListener('click', animateButtonAndShowForm);

loginForm.addEventListener('submit', function(event) {
    event.preventDefault();
    if (!isSetupMode) {
        handleLogin(event);
    }
});