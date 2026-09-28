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
      const promptText = window.I18n ? window.I18n.t('prompt_api_key') : 'Supramemory requiere una clave de API. Ingrésala aquí:';
      const k = window.prompt(promptText);
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
    getTree: () => req('/notes/tree'),
    renameNote: (noteId, newTitle, newPath = null) =>
      req(`/notes/rename?note_id=${encodeURIComponent(noteId)}`, {
        method: 'POST',
        body: JSON.stringify({ new_title: newTitle, new_path: newPath }),
      }),
    getUnlinkedMentions: (noteId) => req(`/notes/${encodeURIComponent(noteId)}/unlinked-mentions`),
    linkMention: (targetId, sourceId, targetTitle) =>
      req(`/notes/${encodeURIComponent(targetId)}/link-mention`, {
        method: 'POST',
        body: JSON.stringify({ source_id: sourceId, target_title: targetTitle }),
      }),
    getDailyNote: () => req('/notes/daily', { method: 'POST' }),
    createFolder: (path) => req('/notes/folders', { method: 'POST', body: JSON.stringify({ path }) }),
    deleteFolder: (path) => req(`/notes/folders?path=${encodeURIComponent(path)}`, { method: 'DELETE' }),
    moveNote: (noteId, targetFolder) =>
      req('/notes/move', { method: 'POST', body: JSON.stringify({ note_id: noteId, target_folder: targetFolder }) }),
    uploadAttachment: async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      const k = getKey();
      const headers = k ? { 'Authorization': `Bearer ${k}` } : {};
      const res = await fetch('/notes/attachments', {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed: ${await res.text()}`);
      return res.json();
    },
    graph: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return req(`/graph${qs ? '?' + qs : ''}`);
    },
    localGraph: (id, depth = 1) => req(`/graph/local/${encodeURIComponent(id)}?depth=${depth}`),
    query: (q, limit = 10) => req(`/query?q=${encodeURIComponent(q)}&limit=${limit}`),
    executeDynamicQuery: (query, limit = 50) =>
      req('/query/execute', { method: 'POST', body: JSON.stringify({ query, limit }) }),
    context: (q, limit = 5) => req(`/context?q=${encodeURIComponent(q)}&limit=${limit}`),
    ingest: () => req('/ingest/vault', { method: 'POST' }),
  };
})();

window.API = API;