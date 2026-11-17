/**
 * CoWork.Hub Slot Booking & Dynamic Calculator
 * 14-hour matrix (08:00 - 22:00) with automatic 20% daily discount (>=6 hours)
 */

document.addEventListener('DOMContentLoaded', function () {
  const slotsMatrix = document.getElementById('slotsMatrix');
  if (!slotsMatrix) return;

  const baseRateEl = document.getElementById('baseRate');
  const hourlyRate = parseFloat(baseRateEl ? baseRateEl.innerText.replace(/\s/g, '') : 350) || 350;

  const slotButtons = slotsMatrix.querySelectorAll('.slot-cell');
  const selectedSlotsInput = document.getElementById('selectedSlotsInput');
  const totalPriceInput = document.getElementById('totalPriceInput');
  const slotCounterText = document.getElementById('slotCounterText');
  const summaryHours = document.getElementById('summaryHours');
  const summaryHourlyBase = document.getElementById('summaryHourlyBase');
  const summaryDiscountRow = document.getElementById('summaryDiscountRow');
  const summaryDiscountVal = document.getElementById('summaryDiscountVal');
  const discountBadge = document.getElementById('discountBadge');
  const summaryServices = document.getElementById('summaryServices');
  const summaryTotalPrice = document.getElementById('summaryTotalPrice');
  const bookingDateInput = document.getElementById('bookingDate');
  const summaryDate = document.getElementById('summaryDate');
  const extraCheckboxes = document.querySelectorAll('.extra-service-checkbox');

  function calculateTotals() {
    const selectedCells = Array.from(slotsMatrix.querySelectorAll('.slot-cell.selected'));
    const selectedHours = selectedCells.map(c => parseInt(c.getAttribute('data-hour'), 10)).sort((a, b) => a - b);
    const count = selectedHours.length;

    // Update hidden inputs
    if (selectedSlotsInput) selectedSlotsInput.value = selectedHours.join(',');
    if (slotCounterText) slotCounterText.innerText = `Выбрано: ${count} ${getHourWord(count)}`;

    // Calculate dates & hours summary
    if (summaryHours) {
      if (count > 0) {
        const minH = String(selectedHours[0]).padStart(2, '0');
        const maxH = String(selectedHours[count - 1] + 1).padStart(2, '0');
        summaryHours.innerText = `${count} ${getHourWord(count)} (${minH}:00–${maxH}:00)`;
      } else {
        summaryHours.innerText = '0 часов (выберите слоты)';
      }
    }

    // Base cost
    const baseTotal = count * hourlyRate;
    if (summaryHourlyBase) {
      summaryHourlyBase.innerText = `${formatNumber(baseTotal)} ₽`;
    }

    // 20% discount if >= 6 hours
    let discount = 0;
    if (count >= 6) {
      discount = Math.round(baseTotal * 0.20);
      if (discountBadge) discountBadge.classList.remove('is-hidden');
      if (summaryDiscountRow) summaryDiscountRow.classList.remove('is-hidden');
      if (summaryDiscountVal) summaryDiscountVal.innerText = `-${formatNumber(discount)} ₽`;
    } else {
      if (discountBadge) discountBadge.classList.add('is-hidden');
      if (summaryDiscountRow) summaryDiscountRow.classList.add('is-hidden');
    }

    // Extra services
    let servicesTotal = 0;
    extraCheckboxes.forEach(cb => {
      if (cb.checked) {
        servicesTotal += parseFloat(cb.getAttribute('data-price') || 0);
      }
    });

    if (summaryServices) {
      summaryServices.innerText = `${formatNumber(servicesTotal)} ₽`;
    }

    // Final total
    const grandTotal = Math.max(0, baseTotal - discount + servicesTotal);
    if (summaryTotalPrice) {
      summaryTotalPrice.innerText = `${formatNumber(grandTotal)} ₽`;
    }
    if (totalPriceInput) {
      totalPriceInput.value = grandTotal;
    }
  }

  // Toggle slot selection on click
  slotButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      if (btn.classList.contains('occupied') || btn.disabled) return;
      btn.classList.toggle('selected');
      calculateTotals();

      const slotError = document.getElementById('slotError');
      if (slotError) slotError.classList.add('is-hidden');
    });
  });

  // Extra service checkbox changes
  extraCheckboxes.forEach(cb => {
    cb.addEventListener('change', calculateTotals);
  });

  // Date input change
  if (bookingDateInput && summaryDate) {
    bookingDateInput.addEventListener('change', function () {
      const parts = bookingDateInput.value.split('-');
      if (parts.length === 3) {
        summaryDate.innerText = `${parts[2]}.${parts[1]}.${parts[0]}`;
      }
    });
  }

  function getHourWord(n) {
    if (n % 10 === 1 && n % 100 !== 11) return 'час';
    if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return 'часа';
    return 'часов';
  }

  function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  // Initial calculation on load
  calculateTotals();
});
