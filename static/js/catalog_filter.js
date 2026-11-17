/**
 * CoWork.Hub Catalog & Interactive Floor Map Logic
 * Handles tab switching (Floor 1 / Floor 2) and desk filtering
 */

document.addEventListener('DOMContentLoaded', function () {
  const tabFloor1 = document.getElementById('tabFloor1');
  const tabFloor2 = document.getElementById('tabFloor2');
  const mapFloor1 = document.getElementById('mapFloor1');
  const mapFloor2 = document.getElementById('mapFloor2');

  if (tabFloor1 && tabFloor2 && mapFloor1 && mapFloor2) {
    tabFloor1.addEventListener('click', function () {
      tabFloor1.classList.add('active');
      tabFloor1.setAttribute('aria-selected', 'true');
      tabFloor2.classList.remove('active');
      tabFloor2.setAttribute('aria-selected', 'false');

      mapFloor1.classList.remove('is-hidden');
      mapFloor2.classList.add('is-hidden');
    });

    tabFloor2.addEventListener('click', function () {
      tabFloor2.classList.add('active');
      tabFloor2.setAttribute('aria-selected', 'true');
      tabFloor1.classList.remove('active');
      tabFloor1.setAttribute('aria-selected', 'false');

      mapFloor2.classList.remove('is-hidden');
      mapFloor1.classList.add('is-hidden');
    });
  }

  // Interactive desk click on SVG map
  const deskPins = document.querySelectorAll('.map-desk-pin');
  deskPins.forEach(function (pin) {
    pin.addEventListener('click', function () {
      const deskNum = pin.getAttribute('data-desk');
      if (deskNum) {
        const card = document.querySelector(`[data-desk-number="${deskNum}"]`);
        if (card) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' });
          card.classList.add('card-highlight');
          setTimeout(() => card.classList.remove('card-highlight'), 1500);
        }
      }
    });
  });
});
