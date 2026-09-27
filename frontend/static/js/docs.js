// Renderiza la documentación interna en el idioma seleccionado (ES, EN, FR, SV)
function loadDocs(force = false) {
  const container = document.getElementById('docs-content');
  if (!container) return;
  const currentLang = window.I18n ? window.I18n.getLang() : 'es';
  if (!force && container.dataset.loadedLang === currentLang) return;
  container.dataset.loadedLang = currentLang;

  const DOCS_BY_LANG = {
    es: `
<h2 id="quickstart">Guía de Inicio Rápido</h2>
<p>Supramemory es un grafo de conocimiento personal con API HTTP. Puedes crear y organizar conocimiento en él, y los agentes de IA lo consultan para tener "memoria persistente".</p>

<h3>1. Obtén tu token</h3>
<p>Ve a la pestaña <strong>API Tokens</strong>, crea uno (al menos permiso <code>read</code> si solo consultas, o <code>write</code> si también vas a crear notas).</p>

<h3>2. Prueba el endpoint más simple</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     https://supramemory.grupogeo.cl/health</code></pre>

<p>Debería devolver:</p>
<pre><code>{"status":"ok","version":"0.1.0","notes_count":0,"links_count":0}</code></pre>

<h3>3. Busca algo</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     "https://supramemory.grupogeo.cl/query?q=m2m&limit=5"</code></pre>

<h3>4. Solicita contexto para inyectar en tu prompt</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     "https://supramemory.grupogeo.cl/context?q=m2m+zendesk+api+keys&limit=3"</code></pre>

<h2 id="obsidian">Capacidades Obsidian</h2>
<p>Supramemory integra las principales funcionalidades de <strong>Obsidian</strong>:</p>
<ul>
  <li>📝 <strong>Editor Live Preview & Split View:</strong> Editor interactivo con doble panel y auto-guardado en tiempo real.</li>
  <li>🔍 <strong>Autocompletado Omni-Suggest:</strong> Escribe <code>[[</code> para autocompletar o crear notas, o <code>#</code> para autocompletar etiquetas.</li>
  <li>📁 <strong>Explorador de Carpetas (File Tree):</strong> Organización jerárquica con subcarpetas en tu vault en disco.</li>
  <li>🔗 <strong>Safe Rename:</strong> Al renombrar una nota, el sistema actualiza automáticamente todos los wikilinks en el vault.</li>
  <li>💡 <strong>Menciones No Enlazadas:</strong> Detección de menciones de texto plano con botón de 1-clic para convertir en wikilink.</li>
  <li>🕸️ <strong>Grafo Local:</strong> Subgrafo centrado en la nota activa con profundidad configurable (1 a 5 saltos) y control de físicas.</li>
  <li>📅 <strong>Notas Diarias (Daily Notes):</strong> Creación y apertura instantánea de la nota de hoy basada en plantillas.</li>
  <li>📎 <strong>Adjuntos e Imágenes:</strong> Pegar con <code>Ctrl+V</code> o arrastrar archivos para guardarlos en <code>/vault/attachments/</code>.</li>
  <li>⚡ <strong>Dataview / Consultas Dinámicas:</strong> Bloques <code>\`\`\`query SELECT ... \`\`\`</code> embebidos que renderizan tablas en vivo.</li>
</ul>

<h2 id="auth">Autenticación</h2>
<p>Todos los endpoints privados requieren el encabezado:</p>
<pre><code>Authorization: Bearer &lt;tu-token&gt;</code></pre>

<p>Los tokens se crean vía interfaz web (pestaña "API Tokens") o vía API con un token de administrador. La clave maestra configurada en <code>API_KEY</code> tiene siempre permiso <code>admin</code>.</p>

<h2 id="endpoints">Endpoints Principales</h2>

<h3>Health & Metadatos</h3>
<table>
<tr><th>Endpoint</th><th>Descripción</th></tr>
<tr><td><code>GET /health</code></td><td>Estado y conteos de notas/enlaces (público)</td></tr>
<tr><td><code>GET /openapi.json</code></td><td>Especificación OpenAPI 3.0 (público)</td></tr>
<tr><td><code>GET /docs</code></td><td>Swagger UI interactivo (público)</td></tr>
</table>

<h3>Notas y Contenido</h3>
<table>
<tr><th>Endpoint</th><th>Permiso</th><th>Descripción</th></tr>
<tr><td><code>GET /notes</code></td><td>read</td><td>Lista notas con filtros opcionales (source, tag, limit, offset)</td></tr>
<tr><td><code>POST /notes</code></td><td>write</td><td>Crea una nota nueva con título, contenido Markdown y etiquetas</td></tr>
<tr><td><code>GET /notes/{id}</code></td><td>read</td><td>Devuelve una nota con contenido plano, enlaces y backlinks</td></tr>
<tr><td><code>GET /notes/{id}/render</code></td><td>read</td><td>Devuelve la nota con HTML renderizado (Callouts, Dataview)</td></tr>
<tr><td><code>PATCH /notes/{id}</code></td><td>write</td><td>Actualiza título, contenido o metadatos de una nota</td></tr>
<tr><td><code>DELETE /notes/{id}</code></td><td>write</td><td>Elimina la nota de la base de datos y del disco</td></tr>
<tr><td><code>POST /notes/rename</code></td><td>write</td><td>Safe Rename: Renombra nota y actualiza wikilinks</td></tr>
<tr><td><code>GET /notes/{id}/unlinked-mentions</code></td><td>read</td><td>Encuentra menciones no enlazadas en otras notas</td></tr>
<tr><td><code>POST /notes/{id}/link-mention</code></td><td>write</td><td>Convierte una mención en texto plano en wikilink</td></tr>
<tr><td><code>POST /notes/daily</code></td><td>write</td><td>Abre o crea la nota diaria de hoy</td></tr>
</table>

<h3>Búsqueda y Grafo</h3>
<table>
<tr><th>Endpoint</th><th>Permiso</th><th>Descripción</th></tr>
<tr><td><code>GET /query?q=...</code></td><td>read</td><td>Búsqueda léxica FTS5 con ranking BM25</td></tr>
<tr><td><code>GET /context?q=...</code></td><td>read</td><td>Devuelve fragmentos optimizados listos para prompts de IA</td></tr>
<tr><td><code>GET /graph</code></td><td>read</td><td>Devuelve nodos y enlaces del grafo completo para D3.js</td></tr>
<tr><td><code>GET /graph/local/{id}?depth=2</code></td><td>read</td><td>Subgrafo local a N saltos centrado en la nota</td></tr>
</table>

<h2 id="agents">Patrón Recomendado para Agentes de IA</h2>
<pre><code class="language-python">import requests

BASE = "https://supramemory.grupogeo.cl"
TOKEN = "sk-TU_TOKEN"

# 1. Obtener contexto antes de responder
res = requests.get(
    f"{BASE}/context?q=arquitectura+docker&limit=3",
    headers={"Authorization": f"Bearer {TOKEN}"}
).json()

# 2. Inyectar en prompt de tu LLM
prompt = f"Contexto de memoria:\\n{res['context_text']}\\n\\nPregunta: ¿Cómo escalar el cluster?"

# 3. Guardar nuevo descubrimiento post-tarea
requests.post(
    f"{BASE}/agents/feed",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "title": "Escalamiento Docker",
        "content": "Revisado quórum en [[Docker Compose]].",
        "topics": ["docker", "infraestructura"]
    }
)</code></pre>
`,
    en: `
<h2 id="quickstart">Quickstart Guide</h2>
<p>Supramemory is a personal knowledge graph with an HTTP API. You create and organize knowledge in it, and autonomous AI agents query it for persistent long-term memory.</p>

<h3>1. Obtain your API token</h3>
<p>Go to the <strong>API Tokens</strong> tab, create one (select at least <code>read</code> scope for querying, or <code>write</code> if creating notes).</p>

<h3>2. Test the health endpoint</h3>
<pre><code>curl -H "Authorization: Bearer sk-YOUR_TOKEN" \\
     https://supramemory.grupogeo.cl/health</code></pre>

<p>Expected response:</p>
<pre><code>{"status":"ok","version":"0.1.0","notes_count":0,"links_count":0}</code></pre>

<h3>3. Search the knowledge base</h3>
<pre><code>curl -H "Authorization: Bearer sk-YOUR_TOKEN" \\
     "https://supramemory.grupogeo.cl/query?q=docker&limit=5"</code></pre>

<h3>4. Fetch prompt-ready context</h3>
<pre><code>curl -H "Authorization: Bearer sk-YOUR_TOKEN" \\
     "https://supramemory.grupogeo.cl/context?q=docker+redis+cluster&limit=3"</code></pre>

<h2 id="obsidian">Obsidian Capabilities</h2>
<p>Supramemory provides full feature parity with <strong>Obsidian</strong>:</p>
<ul>
  <li>📝 <strong>Live Preview & Split View Editor:</strong> Real-time interactive Markdown editor with instant client-side rendering.</li>
  <li>🔍 <strong>Omni-Suggest Autocompletion:</strong> Type <code>[[</code> for note linking or <code>#</code> for tags with full keyboard navigation.</li>
  <li>📁 <strong>File Tree Explorer:</strong> Hierarchical folder navigation mirroring the physical vault on disk.</li>
  <li>🔗 <strong>Safe Rename:</strong> Renaming notes automatically refactors all wikilinks across the vault.</li>
  <li>💡 <strong>Unlinked Mentions:</strong> Detects unlinked text occurrences with a 1-click conversion button to wikilinks.</li>
  <li>🕸️ <strong>Local Graph:</strong> Focused subgraph centered on the active note with configurable depth (1 to 5 hops).</li>
  <li>📅 <strong>Daily Notes:</strong> Instant 1-click access to today's template-based daily note.</li>
  <li>📎 <strong>Attachments & Images:</strong> Paste with <code>Ctrl+V</code> or drag-and-drop directly into <code>/vault/attachments/</code>.</li>
  <li>⚡ <strong>Dataview / Dynamic Queries:</strong> Embedded <code>\`\`\`query SELECT ... \`\`\`</code> blocks rendering live data tables.</li>
</ul>

<h2 id="auth">Authentication</h2>
<p>All private endpoints require the Bearer header:</p>
<pre><code>Authorization: Bearer &lt;your-token&gt;</code></pre>

<p>Tokens can be created via the web interface ("API Tokens" tab) or via REST API with an admin token. The master key configured in <code>API_KEY</code> always has full <code>admin</code> permissions.</p>

<h2 id="endpoints">Key Endpoints</h2>

<h3>Health & Metadata</h3>
<table>
<tr><th>Endpoint</th><th>Description</th></tr>
<tr><td><code>GET /health</code></td><td>Status and total notes/links count (public)</td></tr>
<tr><td><code>GET /openapi.json</code></td><td>OpenAPI 3.0 JSON specification (public)</td></tr>
<tr><td><code>GET /docs</code></td><td>Interactive Swagger UI documentation (public)</td></tr>
</table>

<h3>Notes & Content</h3>
<table>
<tr><th>Endpoint</th><th>Scope</th><th>Description</th></tr>
<tr><td><code>GET /notes</code></td><td>read</td><td>Lists notes with optional filters (source, tag, limit, offset)</td></tr>
<tr><td><code>POST /notes</code></td><td>write</td><td>Creates a new Markdown note in database and on disk</td></tr>
<tr><td><code>GET /notes/{id}</code></td><td>read</td><td>Returns note content, tags, outgoing links, and backlinks</td></tr>
<tr><td><code>GET /notes/{id}/render</code></td><td>read</td><td>Returns fully rendered HTML (Callouts, Dataview, Wikilinks)</td></tr>
<tr><td><code>PATCH /notes/{id}</code></td><td>write</td><td>Updates note title, markdown content, or metadata</td></tr>
<tr><td><code>DELETE /notes/{id}</code></td><td>write</td><td>Permanently deletes note from database and disk</td></tr>
<tr><td><code>POST /notes/rename</code></td><td>write</td><td>Safe Rename: Renames note and refactors wikilinks</td></tr>
<tr><td><code>GET /notes/{id}/unlinked-mentions</code></td><td>read</td><td>Finds plain text mentions of this note in other notes</td></tr>
<tr><td><code>POST /notes/{id}/link-mention</code></td><td>write</td><td>Converts an unlinked mention into an explicit wikilink</td></tr>
<tr><td><code>POST /notes/daily</code></td><td>write</td><td>Opens or creates today's daily note</td></tr>
</table>

<h3>Search & Graph</h3>
<table>
<tr><th>Endpoint</th><th>Scope</th><th>Description</th></tr>
<tr><td><code>GET /query?q=...</code></td><td>read</td><td>Full-text FTS5 search with BM25 ranking</td></tr>
<tr><td><code>GET /context?q=...</code></td><td>read</td><td>Returns high-relevance snippets optimized for AI prompts</td></tr>
<tr><td><code>GET /graph</code></td><td>read</td><td>Returns global graph nodes and edges for D3.js visualization</td></tr>
<tr><td><code>GET /graph/local/{id}?depth=2</code></td><td>read</td><td>Returns local subgraph within N relational hops</td></tr>
</table>

<h2 id="agents">Recommended AI Agent Pattern</h2>
<pre><code class="language-python">import requests

BASE = "https://supramemory.grupogeo.cl"
TOKEN = "sk-YOUR_TOKEN"

# 1. Fetch relevant long-term memory
res = requests.get(
    f"{BASE}/context?q=docker+architecture&limit=3",
    headers={"Authorization": f"Bearer {TOKEN}"}
).json()

# 2. Inject into LLM system prompt
prompt = f"Memory Context:\\n{res['context_text']}\\n\\nTask: Scale the service cluster."

# 3. Save new learning post-task
requests.post(
    f"{BASE}/agents/feed",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={
        "title": "Docker Cluster Scaling",
        "content": "Verified quorum requirements in [[Docker Compose]].",
        "topics": ["docker", "infrastructure"]
    }
)</code></pre>
`,
    fr: `
<h2 id="quickstart">Guide de Démarrage Rapide</h2>
<p>Supramemory est un graphe de connaissances personnelles avec API HTTP. Vous y organisez vos connaissances et vos agents IA s'y connectent pour disposer d'une mémoire persistante à long terme.</p>

<h3>1. Obtenez votre jeton API</h3>
<p>Accédez à l'onglet <strong>Jetons API</strong>, créez-en un (au moins la portée <code>read</code> pour consulter, ou <code>write</code> pour créer des notes).</p>

<h3>2. Testez le point de terminaison santé</h3>
<pre><code>curl -H "Authorization: Bearer sk-VOTRE_JETON" \\
     https://supramemory.grupogeo.cl/health</code></pre>

<h3>3. Recherchez dans la base</h3>
<pre><code>curl -H "Authorization: Bearer sk-VOTRE_JETON" \\
     "https://supramemory.grupogeo.cl/query?q=docker&limit=5"</code></pre>

<h3>4. Obtenez du contexte pour vos prompts</h3>
<pre><code>curl -H "Authorization: Bearer sk-VOTRE_JETON" \\
     "https://supramemory.grupogeo.cl/context?q=docker+redis&limit=3"</code></pre>

<h2 id="obsidian">Fonctionnalités Obsidian</h2>
<ul>
  <li>📝 <strong>Éditeur Live Preview & Split View :</strong> Éditeur Markdown interactif avec aperçu instantané côté client.</li>
  <li>🔍 <strong>Autocomplétion Omni-Suggest :</strong> Tapez <code>[[</code> pour lier des notes ou <code>#</code> pour les tags avec navigation au clavier.</li>
  <li>📁 <strong>Explorateur de dossiers :</strong> Arborescence hiérarchique calquée sur le coffre physique sur disque.</li>
  <li>🔗 <strong>Safe Rename :</strong> Renommer une note met à jour automatiquement tous les wikiliens dans le coffre.</li>
  <li>💡 <strong>Mentions non liées :</strong> Détection automatique des mentions textuelles avec conversion en 1 clic.</li>
  <li>🕸️ <strong>Graphe local :</strong> Sous-graphe centré sur la note active avec profondeur ajustable (1 à 5 sauts).</li>
  <li>📅 <strong>Notes quotidiennes :</strong> Création et ouverture en 1 clic de la note du jour.</li>
  <li>📎 <strong>Pièces jointes :</strong> Collez avec <code>Ctrl+V</code> ou glissez-déposez dans <code>/vault/attachments/</code>.</li>
  <li>⚡ <strong>Dataview dynamique :</strong> Blocs <code>\`\`\`query SELECT ... \`\`\`</code> affichant des tableaux en temps réel.</li>
</ul>

<h2 id="auth">Authentification</h2>
<p>Tous les points d'accès privés requièrent l'en-tête :</p>
<pre><code>Authorization: Bearer &lt;votre-jeton&gt;</code></pre>
`,
    sv: `
<h2 id="quickstart">Snabbstartguide</h2>
<p>Supramemory är en personlig kunskapsgraf med ett HTTP-API. Du skapar och organiserar kunskap i den, och autonoma AI-agenter konsulterar den för bestående långtidsminne.</p>

<h3>1. Hämta din API-token</h3>
<p>Gå till fliken <strong>API-tokens</strong>, skapa en (välj minst behörigheten <code>read</code> för läsning, eller <code>write</code> om du vill skapa anteckningar).</p>

<h3>2. Testa hälsoslutpunkten</h3>
<pre><code>curl -H "Authorization: Bearer sk-DIN_TOKEN" \\
     https://supramemory.grupogeo.cl/health</code></pre>

<h3>3. Sök i kunskapsbasen</h3>
<pre><code>curl -H "Authorization: Bearer sk-DIN_TOKEN" \\
     "https://supramemory.grupogeo.cl/query?q=docker&limit=5"</code></pre>

<h3>4. Hämta sammanhang för AI-prompter</h3>
<pre><code>curl -H "Authorization: Bearer sk-DIN_TOKEN" \\
     "https://supramemory.grupogeo.cl/context?q=docker+cluster&limit=3"</code></pre>

<h2 id="obsidian">Obsidian-funktioner</h2>
<ul>
  <li>📝 <strong>Live Preview & Delad vy:</strong> Interaktiv Markdown-redigerare med direkt förhandsgranskning.</li>
  <li>🔍 <strong>Omni-Suggest automatisk komplettering:</strong> Skriv <code>[[</code> för anteckningslänkar eller <code>#</code> för taggar med piltangentnavigering.</li>
  <li>📁 <strong>Mapputforskare:</strong> Hierarkisk mappstruktur som speglar valvet på disken.</li>
  <li>🔗 <strong>Safe Rename:</strong> Omdöpning av anteckningar uppdaterar automatiskt alla wikilänkar i valvet.</li>
  <li>💡 <strong>Olänkade omnämnanden:</strong> Upptäck textomnämnanden med 1-klicks konvertering till wikilänkar.</li>
  <li>🕸️ <strong>Lokal graf:</strong> Fokuserad delgraf centrerad kring den aktiva anteckningen (1 till 5 hopp).</li>
  <li>📅 <strong>Dagliga anteckningar:</strong> Öppna eller skapa dagens anteckning med 1 klick.</li>
  <li>📎 <strong>Bilagor och bilder:</strong> Klistra in med <code>Ctrl+V</code> eller dra och släpp till <code>/vault/attachments/</code>.</li>
  <li>⚡ <strong>Dataview / Dynamiska frågor:</strong> Inbäddade <code>\`\`\`query SELECT ... \`\`\`</code>-block som visar dynamiska tabeller.</li>
</ul>

<h2 id="auth">Autentisering</h2>
<p>Alla privata slutpunkter kräver auktoriseringshuvudet:</p>
<pre><code>Authorization: Bearer &lt;din-token&gt;</code></pre>
`
  };

  container.innerHTML = DOCS_BY_LANG[currentLang] || DOCS_BY_LANG.es;
}

window.loadDocs = loadDocs;

// Re-renderizar docs automáticamente si cambia el idioma
if (window.I18n && window.I18n.onLangChange) {
  window.I18n.onLangChange(() => {
    const docsTab = document.getElementById('tab-docs');
    if (docsTab && docsTab.classList.contains('active')) {
      loadDocs(true);
    } else {
      const container = document.getElementById('docs-content');
      if (container) container.dataset.loadedLang = '';
    }
  });
}