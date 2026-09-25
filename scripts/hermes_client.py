"""Cliente liviano de Supramemory para el asistente Hermes.

Permite a Hermes:
1. Guardar aprendizajes, observaciones y respuestas en el grafo de conocimiento.
2. Consultar memoria y contexto relevante antes de responder a un usuario.
"""
import os
import json
import urllib.request
import ssl

class HermesSupramemory:
    def __init__(
        self,
        api_url: str = None,
        token: str = None
    ):
        self.api_url = (api_url or os.getenv("SUPRAMEMORY_URL", "https://supramemory.grupogeo.cl")).rstrip("/")
        self.token = token or os.getenv("SUPRAMEMORY_TOKEN", "sk-kR9wxj_H8aqyW5KB2_ogJJHCR5CsaknmafMZNvNczvY")
        
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def _request(self, endpoint: str, method: str = "GET", payload: dict = None):
        url = f"{self.api_url}{endpoint}"
        data = json.dumps(payload).encode("utf-8") if payload else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=self.ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def save_learning(
        self,
        title: str,
        content: str,
        topics: list[str] = None,
        related: list[str] = None,
        kind: str = "observation",
        confidence: float = 0.95
    ) -> dict:
        """Guarda un nuevo aprendizaje u observación de Hermes en Supramemory.
        
        Soporta [[wikilinks]] en el contenido y lista `related` para conectar con nodos existentes.
        """
        payload = {
            "title": title,
            "content": content,
            "topics": topics or ["hermes", "aprendizaje"],
            "kind": kind,
            "confidence": confidence,
            "related": related or []
        }
        return self._request("/agents/feed", method="POST", payload=payload)

    def get_context(self, query: str = None, topics: list[str] = None, limit: int = 5) -> dict:
        """Consulta el contexto relevante almacenado en la memoria viva de Supramemory."""
        params = []
        if topics:
            for t in topics:
                params.append(f"topics={urllib.parse.quote(t)}")
        if query:
            params.append(f"q={urllib.parse.quote(query)}")
        params.append(f"limit={limit}")
        
        qs = "&".join(params)
        return self._request(f"/agents/feed?{qs}", method="GET")


if __name__ == "__main__":
    # Ejemplo de prueba rápida de integración
    client = HermesSupramemory()
    
    print("1. Guardando aprendizaje de prueba desde Hermes...")
    res = client.save_learning(
        title="Hermes: Integración con Supramemory completada",
        content="Hermes está oficialmente conectado con [[Supramemory]] en [[Docker & Dokploy]]. Puede guardar memorias vivas y consultar el [[Ecosistema Desarrollos]].",
        topics=["hermes", "integracion", "memoria"],
        related=["Supramemory", "Docker & Dokploy", "Ecosistema Desarrollos"]
    )
    print("   Respuesta:", res)
    
    print("\n2. Consultando memoria relevante para 'dokploy'...")
    ctx = client.get_context(query="dokploy", limit=3)
    print(f"   Items recuperados: {len(ctx['items'])}")
    for item in ctx["items"]:
        print(f"   - [{item['title']}] {item['snippet'][:100]}...")
