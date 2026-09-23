// Agents feed — para que un agente IA consulte y aporte.
const AgentsFeed = (() => {
  const KEY = localStorage.getItem('supramemory_api_key') || '';

  function authHeaders() {
    return KEY ? { 'Authorization': `Bearer ${KEY}` } : {};
  }

  async function req(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) };
    const res = await fetch(path, { ...opts, headers });
    if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
    return res.json();
  }

  return {
    contribute: (data) => req('/agents/feed', { method: 'POST', body: JSON.stringify(data) }),
    consume: (params = {}) => {
      const qs = new URLSearchParams();
      (params.topics || []).forEach(t => qs.append('topics', t));
      if (params.q) qs.append('q', params.q);
      if (params.limit) qs.append('limit', params.limit);
      return req(`/agents/feed?${qs.toString()}`);
    },
    digest: (params = {}) => {
      const qs = new URLSearchParams();
      (params.topics || []).forEach(t => qs.append('topics', t));
      if (params.limit) qs.append('limit', params.limit);
      return req(`/agents/feed/digest?${qs.toString()}`);
    },
  };
})();

window.AgentsFeed = AgentsFeed;