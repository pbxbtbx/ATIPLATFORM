/* No storage or third-party services. Suggestions use the same server permissions as lists. */
(() => {
  'use strict';
  document.querySelectorAll('form[data-suggest-url]').forEach(form => {
    const input = form.querySelector('[name="q"]');
    const clear = form.querySelector('.search-clear');
    const list = form.querySelector('.search-suggestions');
    const status = form.querySelector('.suggest-status');
    if (!input || !clear || !list || !status) return;
    form.dataset.searchEnhanced = 'true';
    let timer, controller, sequence = 0, active = -1, items = [], composing = false;
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-haspopup', 'listbox');
    input.setAttribute('aria-controls', list.id);
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-describedby', status.id);
    const close = () => {
      list.hidden = true;
      active = -1;
      input.setAttribute('aria-expanded', 'false');
      input.removeAttribute('aria-activedescendant');
    };
    const cancel = () => {
      clearTimeout(timer);
      sequence++;
      if (controller) controller.abort();
      close();
    };
    const choose = index => {
      if (!items[index]) return;
      input.value = items[index].value.slice(0, input.maxLength > 0 ? input.maxLength : 150);
      cancel();
      clear.hidden = !input.value;
      status.textContent = '';
      input.focus();
    };
    const highlight = index => {
      if (!items.length || list.hidden) return;
      active = (index + items.length) % items.length;
      Array.from(list.children).forEach((option, n) => option.setAttribute('aria-selected', String(n === active)));
      const selected = list.children[active];
      input.setAttribute('aria-activedescendant', selected.id);
      selected.scrollIntoView({block: 'nearest'});
    };
    const update = () => {
      clear.hidden = !input.value;
      cancel();
      status.textContent = '';
      if (composing || input.value.trim().length < 2 || input.value.length > 150) return;
      const current = sequence;
      timer = setTimeout(async () => {
        controller = new AbortController();
        try {
          const response = await fetch(form.dataset.suggestUrl, {
            method: 'POST', body: new URLSearchParams(new FormData(form)),
            credentials: 'same-origin', redirect: 'error', cache: 'no-store', signal: controller.signal
          });
          if (!response.ok) throw new Error('suggestions unavailable');
          const data = await response.json();
          if (current !== sequence || document.activeElement !== input) return;
          items = Array.isArray(data.items) ? data.items.slice(0, 8).filter(item => typeof item.label === 'string' && typeof item.value === 'string') : [];
          list.replaceChildren();
          items.forEach((item, index) => {
            const option = document.createElement('li');
            option.id = `${list.id}-${index}`;
            option.setAttribute('role', 'option');
            option.setAttribute('aria-selected', 'false');
            option.textContent = item.label;
            option.addEventListener('pointerdown', event => event.preventDefault());
            option.addEventListener('click', () => choose(index));
            list.append(option);
          });
          list.hidden = !items.length;
          input.setAttribute('aria-expanded', String(!!items.length));
          status.textContent = items.length ? `${form.dataset.suggestCount} ${items.length}` : form.dataset.noResults;
        } catch (error) {
          if (error.name !== 'AbortError' && current === sequence) status.textContent = form.dataset.suggestError;
        }
      }, 200);
    };
    input.addEventListener('input', update);
    input.addEventListener('focus', update);
    input.addEventListener('compositionstart', () => { composing = true; cancel(); });
    input.addEventListener('compositionend', () => { composing = false; update(); });
    input.addEventListener('keydown', event => {
      if (event.isComposing) return;
      if (event.key === 'Escape') { event.preventDefault(); cancel(); status.textContent = ''; }
      else if (!list.hidden && event.key === 'ArrowDown') { event.preventDefault(); highlight(active + 1); }
      else if (!list.hidden && event.key === 'ArrowUp') { event.preventDefault(); highlight(active < 0 ? items.length - 1 : active - 1); }
      else if (!list.hidden && event.key === 'Enter' && active >= 0) { event.preventDefault(); choose(active); }
      else if (event.key === 'Tab') cancel();
    });
    input.addEventListener('blur', () => { cancel(); status.textContent = ''; });
    clear.addEventListener('click', () => {
      input.value = '';
      cancel();
      status.textContent = '';
      clear.hidden = true;
      input.focus();
    });
    form.addEventListener('change', event => { if (event.target !== input) cancel(); });
    form.addEventListener('submit', cancel);
    window.addEventListener('pagehide', cancel);
    clear.hidden = !input.value;
  });
})();
