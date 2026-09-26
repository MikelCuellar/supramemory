// Renderiza la documentación interna (no autogenerada, escrita a mano
// porque OpenAPI ya vive en /docs y /openapi.json de FastAPI).
function loadDocs() {
  const container = document.getElementById('docs-content');
  if (!container || container.dataset.loaded === '1') return;
  container.dataset.loaded = '1';

  container.innerHTML = `
<h2 id="quickstart">Quickstart</h2>
<p>Supramemory es un grafo de conocimiento personal con API HTTP. Vos creás/connues/ais conocimiento en él, y los agentes IA lo consultan para tener "memoria persistente".</p>

<h3>1. Conseguí tu token</h3>
<p>Andá a la pestaña <strong>API Tokens</strong>, creá uno (al menos scope <code>read</code> si solo consultás, <code>write</code> si también vas a crear notas).</p>

<h3>2. Probá el endpoint más simple</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     https://supramemory.grupogeo.cl/health</code></pre>

<p>Debería devolver:</p>
<pre><code>{"status":"ok","version":"0.1.0","notes_count":0,"links_count":0}</code></pre>

<h3>3. Buscá algo</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     "https://supramemory.grupogeo.cl/query?q=m2m&limit=5"</code></pre>

<h3>4. Pedí contexto para inyectar en tu prompt</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     "https://supramemory.grupogeo.cl/context?q=m2m+zendesk+api+keys&limit=3"</code></pre>

<h2 id="obsidian">Capacidades Obsidian</h2>
<p>Supramemory integra las principales funcionalidades de <strong>Obsidian</strong>:</p>
<ul>
  <li>📝 <strong>Editor Live Preview & Split View:</strong> Editor interactivo con doble panel y auto-guardado en tiempo real.</li>
  <li>🔍 <strong>Autocompletado Omni-Suggest:</strong> Escribí <code>[[</code> para autocompletar o crear notas, o <code>#</code> para autocompletar tags.</li>
  <li>📁 <strong>Explorador de Carpetas (File Tree):</strong> Organización jerárquica con subcarpetas en tu vault en disco.</li>
  <li>🔗 <strong>Safe Rename:</strong> Al renombrar una nota, el sistema actualiza automáticamente todos los wikilinks en el vault.</li>
  <li>💡 <strong>Menciones No Enlazadas:</strong> Detección de menciones de texto plano con botón de 1-click para convertir en wikilink.</li>
  <li>🕸️ <strong>Grafo Local:</strong> Subgrafo centrado en la nota activa con profundidad configurable (1 a 5 saltos) y control de físicas.</li>
  <li>📅 <strong>Notas Diarias (Daily Notes):</strong> Creación y apertura instantánea de la nota de hoy basada en plantillas.</li>
  <li>📎 <strong>Adjuntos e Imágenes:</strong> Pegar con <code>Ctrl+V</code> o arrastrar archivos para guardarlos en <code>/vault/attachments/</code>.</li>
  <li>⚡ <strong>Dataview / Consultas Dinámicas:</strong> Bloques <code>```query SELECT ... ```</code> embebidos que renderizan tablas en vivo.</li>
</ul>

<h2 id="auth">Autenticación</h2>
<p>Todos los endpoints (excepto <code>/health</code>, <code>/docs</code>, <code>/openapi.json</code>) requieren:</p>
<pre><code>Authorization: Bearer &lt;tu-token&gt;</code></pre>

<p>Los tokens se crean vía UI (pestaña "API Tokens") o vía API con un admin token. El master key configurado en <code>API_KEY</code> tiene scope <code>admin</code> siempre.</p>

<h2 id="endpoints">Endpoints</h2>

<h3>Health & meta</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>GET /health</code></td><td>Status + counts (público)</td></tr>
<tr><td><code>GET /openapi.json</code></td><td>OpenAPI 3.0 spec (público)</td></tr>
<tr><td><code>GET /docs</code></td><td>Swagger UI (público)</td></tr>
</table>

<h3>Notas</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>GET /notes</code></td><td>Lista (filtros: <code>source</code>, <code>tag</code>, <code>limit</code>, <code>offset</code>)</td></tr>
<tr><td><code>GET /notes/{id}</code></td><td>Lee una nota</td></tr>
<tr><td><code>POST /notes</code></td><td>Crea (write scope)</td></tr>
<tr><td><code>PATCH /notes/{id}</code></td><td>Actualiza (write scope)</td></tr>
<tr><td><code>DELETE /notes/{id}</code></td><td>Borra (write scope)</td></tr>
<tr><td><code>GET /notes/{id}/render</code></td><td>Devuelve content renderizado a HTML</td></tr>
</table>

<h3>Búsqueda</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>GET /query?q=...</code></td><td>Full-text BM25, devuelve array de notas</td></tr>
<tr><td><code>GET /context?q=...&limit=5</code></td><td>Endpoint estrella para inyectar en prompts</td></tr>
</table>

<h3>Graph</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>GET /graph</code></td><td>Nodos + aristas para el graph view (filtros: <code>source</code>, <code>tag</code>, <code>min_degree</code>)</td></tr>
</table>

<h3>Agent feed</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>POST /agents/feed</code></td><td>Agente aporta una nota estructurada (write scope)</td></tr>
<tr><td><code>GET /agents/feed?topics=...</code></td><td>Agente consulta conocimiento relevante (write scope)</td></tr>
<tr><td><code>GET /agents/feed/digest?topics=...</code></td><td>Resumen condensado para prompt</td></tr>
</table>

<h3>Tokens (admin only)</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>POST /tokens</code></td><td>Crea un token (admin)</td></tr>
<tr><td><code>GET /tokens</code></td><td>Lista tokens (admin)</td></tr>
<tr><td><code>POST /tokens/{name}/revoke</code></td><td>Revoca un token (admin)</td></tr>
<tr><td><code>DELETE /tokens/{name}</code></td><td>Borra un token (admin)</td></tr>
</table>

<h2 id="agents">Para agentes IA</h2>

<p>El patrón de uso ideal es:</p>

<h3>Antes de una tarea: pedir contexto</h3>
<pre><code>curl -H "Authorization: Bearer sk-TU_TOKEN" \\
     "https://supramemory.grupogeo.cl/agents/feed/digest?topics=m2m,zendesk&limit=3"

# Devuelve un bloque "digest_text" listo para inyectar en tu prompt</code></pre>

<h3>Durante la tarea: aportar conocimiento</h3>
<pre><code>curl -X POST -H "Authorization: Bearer sk-TU_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{
       "title": "Hallazgo: API keys Zendesk rotan cada 90 días",
       "content": "Confirmado en dashboard de Zendesk... #zendesk #operaciones",
       "topics": ["zendesk", "operaciones"],
       "kind": "observation",
       "confidence": 0.9,
       "related": ["M2M Zendesk API"]
     }' \\
     "https://supramemory.grupogeo.cl/agents/feed"</code></pre>

<h3>El campo "kind"</h3>
<table style="width:100%; font-size:12px; border-collapse:collapse; margin:8px 0;">
<tr><td><code>observation</code></td><td>Dato nuevo observado</td></tr>
<tr><td><code>summary</code></td><td>Resumen de algo</td></tr>
<tr><td><code>link</code></td><td>Referencia a un recurso externo</td></tr>
<tr><td><code>question</code></td><td>Pregunta abierta</td></tr>
<tr><td><code>answer</code></td><td>Respuesta a una pregunta</td></tr>
</table>

<h3>El campo "confidence"</h3>
<p>0.0 = no confiable (especulación), 1.0 = confirmado. Útil para que otros agentes filtren.</p>

<h2 id="scopes">Scopes y seguridad</h2>
<ul>
<li><strong>read</strong>: GET endpoints (leer grafo, buscar)</li>
<li><strong>write</strong>: read + POST/PATCH/DELETE (crear/modificar notas)</li>
<li><strong>admin</strong>: write + gestión de tokens + ingest</li>
</ul>
<p>El <code>API_KEY</code> configurado como variable de entorno siempre tiene scope <code>admin</code>.</p>

<p>Buenas prácticas:</p>
<ul>
<li>Cada agente debería tener su propio token (scope mínimo necesario)</li>
<li>Para read-only (ej: agente que solo busca), dar solo scope <code>read</code></li>
<li>Rotar tokens cada 90 días usando <code>expires_at</code></li>
<li>Si un token se compromete, revocarlo desde la UI</li>
</ul>

<h2 id="examples">Ejemplos</h2>

<h3>Bash: buscar y mostrar título + snippet</h3>
<pre><code>TOKEN="sk-TU_TOKEN"
BASE="https://supramemory.grupogeo.cl"

# Buscar
curl -s -H "Authorization: Bearer $TOKEN" \\
     "$BASE/query?q=m2m&limit=3" | \\
  python3 -c "
import sys, json
for n in json.load(sys.stdin):
    print(f\"# {n['title']}\")
    print(n['snippet'][:150], '\\n')
"</code></pre>

<h3>Python: cliente completo</h3>
<pre><code>import requests

TOKEN = "sk-TU_TOKEN"
BASE = "https://supramemory.grupogeo.cl"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Buscar
r = requests.get(f"{BASE}/context", params={"q": "m2m", "limit": 3}, headers=HEADERS)
context = r.json()
for item in context["items"]:
    print(f"# {item['title']}")
    print(item["snippet"])

# Aportar
r = requests.post(f"{BASE}/agents/feed", headers=HEADERS, json={
    "title": "Mi descubrimiento",
    "content": "Texto en Markdown con [[wikilinks]] y #tags",
    "topics": ["descubrimiento"],
    "kind": "observation",
})
print(r.json())</code></pre>

<h3>Python: contexto automático en cada llamada</h3>
<pre><code>import requests
import functools

BASE = "https://supramemory.grupogeo.cl"
TOKEN = "sk-TU_TOKEN"

def with_context(topics):
    """Decorator: agrega contexto de Supramemory a cada llamada al LLM."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            r = requests.get(
                f"{BASE}/agents/feed/digest",
                params={"topics": topics, "limit": 3},
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
            context = r.json()["meta"]["digest_text"]
            return fn(context + "\\n\\n" + str(args), **kwargs)
        return wrapper
    return decorator

@with_context(["m2m", "zendesk"])
def handle_question(question):
    # Acá llamás a tu LLM con la question + contexto
    pass</code></pre>
  `;
}
window.loadDocs = loadDocs;