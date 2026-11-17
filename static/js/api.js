/**
 * CoWork.Hub JSON API Client (Fetch API)
 * Handles 1-click booking extension with loading spinner and live DOM updates
 */

document.addEventListener('DOMContentLoaded', function () {
  const btnExtend = document.getElementById('btnExtendBooking');
  if (!btnExtend) return;

  btnExtend.addEventListener('click', function () {
    const bookingId = btnExtend.getAttribute('data-booking-id');
    if (!bookingId) return;

    const spinner = document.getElementById('extendSpinner');
    const btnText = btnExtend.querySelector('.btn-text');

    // 1. Show loading state
    btnExtend.disabled = true;
    if (spinner) spinner.classList.remove('is-hidden');
    if (btnText) btnText.innerText = 'Продлеваем...';

    // Get CSRF token from cookie or meta
    const csrfToken = getCookie('csrftoken') || '';

    // 2. Fetch call to custom Django API endpoint
    fetch(`/api/bookings/${bookingId}/extend/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ hours: 1 })
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(errData => {
            throw new Error(errData.error || 'Ошибка при продлении бронирования');
          });
        }
        return response.json();
      })
      .then(data => {
        // 3. Update DOM with response data
        if (data.success) {
          const activeEndTime = document.getElementById('activeEndTime');
          if (activeEndTime && data.new_end_time) {
            activeEndTime.innerText = data.new_end_time;
          }

          const countdownText = document.getElementById('countdownText');
          if (countdownText) {
            countdownText.innerText = '1 час 42 минуты';
            countdownText.classList.remove('text-warning');
            countdownText.classList.add('text-success');
          }

          const countdownFill = document.getElementById('countdownFill');
          if (countdownFill) {
            countdownFill.style.width = '85%';
            countdownFill.style.backgroundColor = 'var(--color-success)';
          }

          alert(data.message || 'Бронирование успешно продлено на 1 час!');
        }
      })
      .catch(error => {
        alert(error.message);
      })
      .finally(() => {
        // 4. Restore button state
        btnExtend.disabled = false;
        if (spinner) spinner.classList.add('is-hidden');
        if (btnText) btnText.innerText = '⚡ Продлить на 1 час (350 ₽)';
      });
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
