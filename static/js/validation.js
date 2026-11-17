/**
 * CoWork.Hub Client-Side Form Validation (Занятие 9)
 * Validates required fields, email format, phone format, and string length
 */

document.addEventListener('DOMContentLoaded', function () {
  // Regex patterns
  const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  const PHONE_REGEX = /^(?:\+7|8)?[\s(-]*\d{3}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}$/;

  // Helper to show/hide errors
  function setFieldError(inputEl, errorEl, isError, message) {
    if (!inputEl) return;
    if (isError) {
      inputEl.classList.add('is-invalid');
      if (errorEl) {
        if (message) errorEl.innerText = message;
        errorEl.classList.remove('is-hidden');
      }
    } else {
      inputEl.classList.remove('is-invalid');
      if (errorEl) {
        errorEl.classList.add('is-hidden');
      }
    }
  }

  // 1. Validation for Booking Form (#bookingForm)
  const bookingForm = document.getElementById('bookingForm');
  if (bookingForm) {
    const dateInput = document.getElementById('bookingDate');
    const dateError = document.getElementById('dateError');

    const nameInput = document.getElementById('residentName');
    const nameError = document.getElementById('nameError');

    const phoneInput = document.getElementById('residentPhone');
    const phoneError = document.getElementById('phoneError');

    const emailInput = document.getElementById('residentEmail');
    const emailError = document.getElementById('emailError');

    const slotError = document.getElementById('slotError');
    const slotsMatrix = document.getElementById('slotsMatrix');

    // Live validation on blur
    if (nameInput) {
      nameInput.addEventListener('blur', () => {
        const valid = nameInput.value.trim().length >= 3;
        setFieldError(nameInput, nameError, !valid, 'Имя должно содержать не менее 3 символов');
      });
      nameInput.addEventListener('input', () => {
        if (nameInput.classList.contains('is-invalid') && nameInput.value.trim().length >= 3) {
          setFieldError(nameInput, nameError, false);
        }
      });
    }

    if (phoneInput) {
      phoneInput.addEventListener('blur', () => {
        const valid = PHONE_REGEX.test(phoneInput.value.trim());
        setFieldError(phoneInput, phoneError, !valid, 'Введите телефон в формате +7 (xxx) xxx-xx-xx');
      });
      phoneInput.addEventListener('input', () => {
        if (phoneInput.classList.contains('is-invalid') && PHONE_REGEX.test(phoneInput.value.trim())) {
          setFieldError(phoneInput, phoneError, false);
        }
      });
    }

    if (emailInput) {
      emailInput.addEventListener('blur', () => {
        const valid = EMAIL_REGEX.test(emailInput.value.trim());
        setFieldError(emailInput, emailError, !valid, 'Введите корректный адрес электронной почты');
      });
      emailInput.addEventListener('input', () => {
        if (emailInput.classList.contains('is-invalid') && EMAIL_REGEX.test(emailInput.value.trim())) {
          setFieldError(emailInput, emailError, false);
        }
      });
    }

    // Submit validation
    bookingForm.addEventListener('submit', function (e) {
      let hasErrors = false;

      // Date check
      if (dateInput && !dateInput.value) {
        setFieldError(dateInput, dateError, true, 'Укажите дату бронирования');
        hasErrors = true;
      }

      // Name check
      if (nameInput && nameInput.value.trim().length < 3) {
        setFieldError(nameInput, nameError, true, 'Имя должно содержать не менее 3 символов');
        hasErrors = true;
      }

      // Phone check
      if (phoneInput && !PHONE_REGEX.test(phoneInput.value.trim())) {
        setFieldError(phoneInput, phoneError, true, 'Введите корректный номер телефона');
        hasErrors = true;
      }

      // Email check
      if (emailInput && !EMAIL_REGEX.test(emailInput.value.trim())) {
        setFieldError(emailInput, emailError, true, 'Введите корректный email');
        hasErrors = true;
      }

      // Slots check
      if (slotsMatrix) {
        const selected = slotsMatrix.querySelectorAll('.slot-cell.selected');
        if (selected.length === 0) {
          if (slotError) slotError.classList.remove('is-hidden');
          hasErrors = true;
        } else {
          if (slotError) slotError.classList.add('is-hidden');
        }
      }

      if (hasErrors) {
        e.preventDefault();
        const firstInvalid = bookingForm.querySelector('.is-invalid');
        if (firstInvalid) {
          firstInvalid.focus();
        }
      }
    });
  }

  // 2. Validation for Checkout Form (#checkoutForm)
  const checkoutForm = document.getElementById('checkoutForm');
  if (checkoutForm) {
    const payerName = document.getElementById('payerName');
    const payerNameError = document.getElementById('payerNameError');

    const payerEmail = document.getElementById('payerEmail');
    const payerEmailError = document.getElementById('payerEmailError');

    const agreeTerms = document.getElementById('agreeTerms');
    const agreeError = document.getElementById('agreeError');

    checkoutForm.addEventListener('submit', function (e) {
      let hasErrors = false;

      if (payerName && payerName.value.trim().length < 3) {
        setFieldError(payerName, payerNameError, true, 'Укажите имя плательщика (от 3 символов)');
        hasErrors = true;
      }

      if (payerEmail && !EMAIL_REGEX.test(payerEmail.value.trim())) {
        setFieldError(payerEmail, payerEmailError, true, 'Введите корректный адрес электронной почты');
        hasErrors = true;
      }

      if (agreeTerms && !agreeTerms.checked) {
        if (agreeError) agreeError.classList.remove('is-hidden');
        hasErrors = true;
      } else if (agreeError) {
        agreeError.classList.add('is-hidden');
      }

      if (hasErrors) {
        e.preventDefault();
        const firstInvalid = checkoutForm.querySelector('.is-invalid');
        if (firstInvalid) firstInvalid.focus();
      }
    });
  }
});
