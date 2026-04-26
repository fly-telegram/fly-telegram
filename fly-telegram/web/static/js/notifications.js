function showNotification(message, duration = 3000) {
  const notificationContainer = document.getElementById('notification-container');
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;

  notificationContainer.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'fadeOut 0.5s ease-out';
    setTimeout(() => {
      notification.remove();
    }, 500);
  }, duration);
}

export { showNotification };