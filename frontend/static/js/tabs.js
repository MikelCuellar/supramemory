// Tabs: switch entre Graph / Tokens / Docs
const Tabs = (() => {
  function init() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetId = `tab-${tab.dataset.tab}`;
        // Update buttons
        tabs.forEach(t => t.classList.toggle('active', t === tab));
        // Update panels
        document.querySelectorAll('.tab-panel').forEach(p => {
          p.classList.toggle('active', p.id === targetId);
        });
        // Trigger resize on graph if switching back
        if (targetId === 'tab-graph' && window.Graph && window.Graph.reheat) {
          setTimeout(() => window.Graph.reheat(0.3), 50);
        }
        // Load tokens when entering tab
        if (targetId === 'tab-tokens' && window.loadTokens) {
          window.loadTokens();
        }
        // Load docs when entering tab
        if (targetId === 'tab-docs' && window.loadDocs) {
          window.loadDocs();
        }
      });
    });
  }
  return { init };
})();

document.addEventListener('DOMContentLoaded', Tabs.init);