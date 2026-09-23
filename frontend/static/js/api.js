// Cliente API para Supramemory
const API = (() => {
  const KEY_STORAGE = 'supramemory_api_key';

  function setKey(k) {
    if (!k) {
      localStorage.removeItem(KEY_STORAGE);
    } else {
      localStorage.setItem(KEY_STORAGE, k);
    }
  }

  function getKey() {
    return localStorage.getItem(KEY_STORAGE) || '';
  }

  function authHeaders() {
    const k = getKey();
    return k ? { 'Authorization': `Bearer ${k}` } : {};
  }

  async function req(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) };
    const res = await fetch(path, { ...opts, headers });
    if (res.status === 401 || res.status === 403) {
      // pedir key UNA vez, guardarla, y reintentar
      const k = window.prompt('Supramemory requiere API key. Pegala aca:');
      if (k) {
        setKey(k);
        return req(path, opts);  // reintento con la nueva key
      }
      throw new Error('Unauthorized - no API key provided');
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
    getKey,
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