/**
 * CoWork.Hub Main JavaScript
 * Handles navigation drawer, alert dismiss, modals, and global UI interactions
 */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Hamburger Menu Toggle
  const burgerBtn = document.getElementById('burgerBtn');
  const mobileDrawer = document.getElementById('mobileDrawer');

  if (burgerBtn && mobileDrawer) {
    burgerBtn.addEventListener('click', function () {
      const isExpanded = burgerBtn.getAttribute('aria-expanded') === 'true';
      burgerBtn.setAttribute('aria-expanded', !isExpanded);
      mobileDrawer.classList.toggle('open');
      document.body.classList.toggle('drawer-open');
    });

    // Close drawer when clicking outside or pressing Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileDrawer.classList.contains('open')) {
        burgerBtn.setAttribute('aria-expanded', 'false');
        mobileDrawer.classList.remove('open');
        document.body.classList.remove('drawer-open');
      }
    });
  }

  // 2. Alert Dismiss Handlers
  const alertCloseButtons = document.querySelectorAll('.alert-close');
  alertCloseButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      const alert = button.closest('.alert');
      if (alert) {
        alert.style.transition = 'opacity 200ms ease, transform 200ms ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function () {
          alert.remove();
        }, 200);
      }
    });
  });

  // 3. Modal helper functions
  window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  };

  window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  // Close modals on backdrop click or close button
  document.querySelectorAll('.modal-overlay').forEach(function (modal) {
    modal.addEventListener('click', function (e) {
      if (e.target === modal || e.target.classList.contains('modal-close') || e.target.closest('.modal-close')) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    });
  });
});
