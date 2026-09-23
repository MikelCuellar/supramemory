// Cliente API para Supramemory
const API = (() => {
  const KEY = localStorage.getItem('supramemory_api_key') || '';

  function setKey(k) {
    localStorage.setItem('supramemory_api_key', k);
  }

  function authHeaders() {
    return KEY ? { 'Authorization': `Bearer ${KEY}` } : {};
  }

  async function req(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) };
    const res = await fetch(path, { ...opts, headers });
    if (res.status === 401 || res.status === 403) {
      const k = prompt('Supramemory requiere API key. Pegala acá:');
      if (k) {
        setKey(k);
        return req(path, opts);
      }
      throw new Error('Unauthorized');
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status}: ${text}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  return {
    setKey,
    health: () => req('/health'),
    listNotes: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return req(`/notes${qs ? '?' + qs : ''}`);
    },
    getNote: (id) => req(`/notes/${id}`),
    getRendered: (id) => req(`/notes/${id}/render`),
    createNote: (data) => req('/notes', { method: 'POST', body: JSON.stringify(data) }),
    updateNote: (id, data) => req(`/notes/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    deleteNote: (id) => req(`/notes/${id}`, { method: 'DELETE' }),
    graph: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return req(`/graph${qs ? '?' + qs : ''}`);
    },
    query: (q, limit = 10) => req(`/query?q=${encodeURIComponent(q)}&limit=${limit}`),
    context: (q, limit = 5) => req(`/context?q=${encodeURIComponent(q)}&limit=${limit}`),
    ingest: () => req('/ingest/vault', { method: 'POST' }),
  };
})();