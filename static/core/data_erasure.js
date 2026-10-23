(() => {
  'use strict';
  const inputs = Array.from(document.querySelectorAll('.erasure-selection input[name="student"]'));
  const count = document.querySelector('[data-erasure-count]');
  const update = () => { if (count) count.textContent = String(inputs.filter(input => input.checked).length); };
  document.querySelectorAll('[data-erasure-select]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      inputs.forEach(input => { input.checked = button.dataset.erasureSelect === 'all'; });
      update();
    });
  });
  inputs.forEach(input => input.addEventListener('change', update));
  update();
})();
