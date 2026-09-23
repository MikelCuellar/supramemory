// Módulo de gestión de tokens — admin only.
// Permite crear, listar, revocar y borrar tokens de la DB.

const Tokens = (() => {
  const KEY = localStorage.getItem('supramemory_api_key') || '';

  function authHeaders() {
    return KEY ? { 'Authorization': `Bearer ${KEY}` } : {};
  }

  async function req(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) };
    const res = await fetch(path, { ...opts, headers });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status}: ${text}`);
    }
    if (res.status === 204) return null;
    return res.json();
  }

  return {
    list: (includeRevoked = false) =>
      req(`/tokens?include_revoked=${includeRevoked}`),
    create: (name, scopes, expiresAt = null) =>
      req('/tokens', { method: 'POST', body: JSON.stringify({ name, scopes, expires_at: expiresAt }) }),
    revoke: (name) => req(`/tokens/${encodeURIComponent(name)}/revoke`, { method: 'POST' }),
    delete: (name) => req(`/tokens/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  };
})();

window.Tokens = Tokens;