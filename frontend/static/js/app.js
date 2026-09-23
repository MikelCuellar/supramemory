// App entry point — coordina filtros, búsqueda, graph view, panel lateral.
(async function () {
  const sidePanel = document.getElementById('side-panel');
  const panelContent = document.getElementById('panel-content');
  const legendItems = document.getElementById('legend-items');
  const searchInput = document.getElementById('search-input');

  // Init grafo
  Graph.init(async (node) => {
    if (!node) {
      sidePanel.classList.add('collapsed');
      Graph.setSelectedStatus('Nada seleccionado');
      return;
    }
    Graph.setSelectedStatus(`Seleccionado: ${node.label}`);
    await openNodePanel(node);
  });

  // Init filtros
  await Filters.init();
  Filters.onChange((state) => {
    loadGraph();
  });

  // Close panel
  document.getElementById('close-panel').addEventListener('click', () => {
    Graph.deselect();
  });

  // Search
  let searchTimer = null;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      Graph.highlightByText(e.target.value.trim());
    }, 200);
  });
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      Graph.highlightByText(e.target.value.trim());
    }
  });

  // Cargar grafo inicial
  await loadGraph();

  async function loadGraph() {
    try {
      const params = {};
      const f = Filters.get();
      if (f.source) params.source = f.source;
      if (f.tag) params.tag = f.tag;
      const data = await API.graph(params);
      Graph.render(data);
      updateLegend(data.nodes);
    } catch (e) {
      console.error('Load graph failed:', e);
      document.getElementById('status-count').textContent = `Error: ${e.message}`;
    }
  }

  async function openNodePanel(node) {
    panelContent.innerHTML = '<div class="meta">cargando…</div>';
    sidePanel.classList.remove('collapsed');

    try {
      const rendered = await API.getRendered(node.id);
      panelContent.innerHTML = `
        <h2>${escapeHtml(rendered.title)}</h2>
        <div class="meta">
          <span>id: ${escapeHtml(rendered.id)}</span>
          ${rendered.tags.length ? `<span>· ${rendered.tags.length} tags</span>` : ''}
        </div>
        ${rendered.tags.length ? `
          <div class="tags">
            ${rendered.tags.map(t => `<span class="tag">#${escapeHtml(t)}</span>`).join('')}
          </div>
        ` : ''}
        <div class="body">${rendered.html}</div>
        ${rendered.backlinks.length ? `
          <div class="backlinks">
            <h4>Backlinks (${rendered.backlinks.length})</h4>
            ${rendered.backlinks.map(b => `<a href="#" data-backlink="${escapeHtml(b)}">${escapeHtml(b)}</a>`).join('')}
          </div>
        ` : ''}
      `;

      // Click en backlink → carga ese nodo
      panelContent.querySelectorAll('[data-backlink]').forEach(el => {
        el.addEventListener('click', async (e) => {
          e.preventDefault();
          const targetId = el.dataset.backlink;
          const targetNode = (await API.graph()).nodes.find(n => n.id === targetId);
          if (targetNode) Graph.selectNode(targetNode);
        });
      });
    } catch (e) {
      panelContent.innerHTML = `<div class="meta">Error: ${escapeHtml(e.message)}</div>`;
    }
  }

  function updateLegend(nodes) {
    const sources = new Map();
    nodes.forEach(n => {
      sources.set(n.source, (sources.get(n.source) || 0) + 1);
    });
    legendItems.innerHTML = '';
    Array.from(sources.entries()).sort().forEach(([src, count]) => {
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = `
        <span class="legend-dot" style="background: ${sourceColor(src)}"></span>
        <span>${src}</span>
        <span style="color: var(--fg-muted); margin-left: auto;">${count}</span>
      `;
      legendItems.appendChild(item);
    });
  }

  function sourceColor(source) {
    const colors = {
      manual: '#a8e10c',
      vault: '#a8e10c',
      telegram: '#4a9eff',
      pdf: '#ff8c42',
      session: '#b56cff',
      email: '#ffd84a',
    };
    return colors[source] || '#888';
  }

  function escapeHtml(s) {
    if (!s) return '';
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
})();

// === Tokens tab logic ===
async function loadTokens() {
  const tbody = document.getElementById('tokens-tbody');
  if (!tbody) return;
  const showRevoked = document.getElementById('show-revoked').checked;
  try {
    const tokens = await Tokens.list(showRevoked);
    if (!tokens.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="muted center">No hay tokens todavía. Creá uno arriba.</td></tr>';
      return;
    }
    tbody.innerHTML = tokens.map(t => {
      const scopes = t.scopes.split(',').map(s =>
        `<span class="scope-tag">${s.trim()}</span>`
      ).join(' ');
      const status = t.revoked
        ? '<span class="status-revoked">revoked</span>'
        : '<span class="status-active">active</span>';
      const actions = t.revoked
        ? `<button class="btn-mini danger" onclick="deleteToken('${escapeAttr(t.name)}')">Borrar</button>`
        : `<button class="btn-mini" onclick="revokeToken('${escapeAttr(t.name)}')">Revocar</button>
           <button class="btn-mini danger" onclick="deleteToken('${escapeAttr(t.name)}')">Borrar</button>`;
      return `<tr>
        <td><strong>${escapeHtml(t.name)}</strong></td>
        <td>${scopes}</td>
        <td>${t.created_at ? t.created_at.substring(0, 19) : '—'}</td>
        <td>${t.last_used_at ? t.last_used_at.substring(0, 19) : '—'}</td>
        <td>${t.expires_at || '—'}</td>
        <td>${status}</td>
        <td>${actions}</td>
      </tr>`;
    }).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="muted center">Error: ${escapeHtml(e.message)}</td></tr>`;
  }
}

async function revokeToken(name) {
  if (!confirm(`Revocar token "${name}"? Queda en la DB pero no se puede usar más.`)) return;
  try {
    await Tokens.revoke(name);
    await loadTokens();
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

async function deleteToken(name) {
  if (!confirm(`Borrar token "${name}" permanentemente? Esta acción no se puede deshacer.`)) return;
  try {
    await Tokens.delete(name);
    await loadTokens();
  } catch (e) {
    alert(`Error: ${e.message}`);
  }
}

function escapeAttr(s) {
  return String(s).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// Hook form
document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('token-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('token-name').value.trim();
      const scopes = Array.from(document.getElementById('token-scopes').selectedOptions)
        .map(o => o.value);
      const expiry = document.getElementById('token-expiry').value;
      const expires_at = expiry ? new Date(expiry).toISOString() : null;

      try {
        const result = await Tokens.create(name, scopes, expires_at);
        document.getElementById('token-plain').textContent = result.token;
        document.getElementById('token-result').classList.remove('hidden');
        form.reset();
        await loadTokens();
      } catch (err) {
        alert(`Error creando token: ${err.message}`);
      }
    });
  }

  document.getElementById('copy-token')?.addEventListener('click', () => {
    const text = document.getElementById('token-plain').textContent;
    navigator.clipboard.writeText(text);
    alert('Token copiado al portapapeles');
  });

  document.getElementById('token-result-close')?.addEventListener('click', () => {
    document.getElementById('token-result').classList.add('hidden');
  });

  document.getElementById('show-revoked')?.addEventListener('change', loadTokens);
});

window.loadTokens = loadTokens;
window.revokeToken = revokeToken;
window.deleteToken = deleteToken;