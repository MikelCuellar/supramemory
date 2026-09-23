// Filtros: source + tag. Popula los selects y maneja cambios.
const Filters = (() => {
  const state = { source: '', tag: '' };
  const listeners = [];

  function notify() {
    listeners.forEach(fn => fn(state));
  }

  async function init() {
    try {
      const notes = await API.listNotes({ limit: 500 });
      const sources = new Set();
      const tags = new Set();
      notes.forEach(n => {
        sources.add(n.source);
        (n.tags || []).forEach(t => tags.add(t));
      });

      const sel = document.getElementById('filter-source');
      Array.from(sources).sort().forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        sel.appendChild(opt);
      });
      sel.addEventListener('change', (e) => {
        state.source = e.target.value;
        notify();
      });

      const tagSel = document.getElementById('filter-tag');
      Array.from(tags).sort().forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = `#${t}`;
        tagSel.appendChild(opt);
      });
      tagSel.addEventListener('change', (e) => {
        state.tag = e.target.value;
        notify();
      });
    } catch (e) {
      console.error('Filters init failed:', e);
    }
  }

  function onChange(fn) {
    listeners.push(fn);
  }

  function get() { return { ...state }; }

  return { init, onChange, get };
})();