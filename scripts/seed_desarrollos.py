"""Script para poblar Supramemory con la información del workspace /Users/mikel/Documents/Desarrollos."""
import os
import urllib.request
import json

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "WmGIqEjseUTEimA3k93cGjk3jw5v5PYp")

notes = [
    {
        "id": "desarrollos-overview",
        "title": "Ecosistema Desarrollos",
        "source": "vault",
        "tags": ["overview", "hub", "desarrollos"],
        "content": """Centro principal de proyectos en `/Users/mikel/Documents/Desarrollos`. Engloba plataformas de telemetría IoT, Inteligencia Artificial, monitoreo ganadero y gestión de tareas:

- [[GEOTASK]]: Plataforma multi-tenant de gestión de tareas con [[GeotaskAPI]], [[GeotaskWEB]] y [[GeotaskMobile]].
- [[GeoIA]]: Gateway empresarial de IA para atención a clientes con [[Vercel AI SDK]] y [[Agentes IA]].
- [[Rastreo Bovino]]: Plataforma GanadoGPS para monitoreo en tiempo real de ganado con [[React]] y [[Mapas Leaflet]].
- [[SST310U Listener]]: Receptor TCP satelital en [[Go]] para dispositivos SST310U.
- [[Listener Telemetria]]: Receptor SOAP XML de telemetría GPS en [[Go]] con [[PostgreSQL]].
- [[Hello Crea Mundo]]: Sistema de búsqueda de patentes de vehículos chilenos (APS).
- [[Supramemory]]: Personal Knowledge Graph e integración con [[Agentes IA]] desplegado en [[Docker & Dokploy]]."""
    },
    {
        "id": "geotask",
        "title": "GEOTASK",
        "source": "vault",
        "tags": ["project", "tasks", "mobile", "web", "api"],
        "content": """Plataforma multi-tenant de gestión de tareas geolocalizadas y personal en terreno. Dividida en tres componentes principales:

1. [[GeotaskAPI]]: Backend en [[Node.js]] y [[Express]].
2. [[GeotaskWEB]]: Portal de administración en [[React]] + [[Vite]].
3. [[GeotaskMobile]]: App móvil offline-first en [[Expo React Native]].

Integrado con base de datos [[PostgreSQL]] y desplegado mediante [[Docker & Dokploy]]. Se conecta con el ecosistema de [[Ecosistema Desarrollos]]."""
    },
    {
        "id": "geotask-api",
        "title": "GeotaskAPI",
        "source": "vault",
        "tags": ["backend", "express", "geotask"],
        "content": """REST API para la plataforma [[GEOTASK]]. Construida en [[Node.js]] con [[Express]] y [[PostgreSQL]].

- Autenticación y gestión de organizaciones multi-tenant.
- Sincronización de tareas enviadas desde [[GeotaskMobile]].
- Endpoints de consulta para el portal de administración [[GeotaskWEB]]."""
    },
    {
        "id": "geotask-web",
        "title": "GeotaskWEB",
        "source": "vault",
        "tags": ["frontend", "react", "geotask"],
        "content": """Portal web administrativo para [[GEOTASK]].

- **Stack:** [[React]] 19, [[Vite]], Tailwind CSS.
- **Funcionalidad:** Visualización en mapa de cuadrillas en terreno, asignación de tareas y reportes.
- Consume la API REST de [[GeotaskAPI]]."""
    },
    {
        "id": "geotask-mobile",
        "title": "GeotaskMobile",
        "source": "vault",
        "tags": ["mobile", "react-native", "geotask"],
        "content": """Aplicación móvil offline-first para técnicos y personal de campo de [[GEOTASK]].

- **Stack:** [[Expo React Native]], TypeScript.
- **Sincronización:** Funciona sin conexión a internet y sincroniza al detectar red hacia [[GeotaskAPI]].
- Soporte para GPS en segundo plano y captura de fotos."""
    },
    {
        "id": "geoia",
        "title": "GeoIA",
        "source": "vault",
        "tags": ["ai", "gateway", "customer-support", "typescript"],
        "content": """Enterprise AI Customer Support Gateway. Sistema de chat con IA de nivel empresarial para soporte al cliente.

- **Stack:** TypeScript, [[Vercel AI SDK]], Node.js, PNPM.
- **Características:** Integración directa con APIs de terceros, plataformas IoT, CRMs y sistemas de tracking GPS.
- **Bucle de Agentes:** Implementa bucles autónomos de [[Agentes IA]] conectados a la memoria de [[Supramemory]]."""
    },
    {
        "id": "rastreo-bovino",
        "title": "Rastreo Bovino",
        "source": "vault",
        "tags": ["iot", "gps", "react", "livestock"],
        "content": """Sistema de Monitoreo de Comportamiento Bovino (**GanadoGPS**). Plataforma web para rastrear y gestionar ganado en tiempo real.

- **Stack:** [[React]], TypeScript, [[Vite]], Tailwind CSS, shadcn/ui.
- **Mapas & Gráficos:** [[Mapas Leaflet]] (React Leaflet) y Recharts para telemetría.
- **Conectividad:** Recibe datos procesados desde [[SST310U Listener]] y [[Listener Telemetria]] con almacenamiento en [[PostgreSQL]]."""
    },
    {
        "id": "sst310u-listener",
        "title": "SST310U Listener",
        "source": "vault",
        "tags": ["tcp", "satellite", "go", "iot"],
        "content": """Servicio TCP en tiempo real para recepción de datos del terminal satelital SST310U.

- **Lenguaje:** [[Go]] (Golang).
- **Puerto:** Escucha TCP en puerto 5028.
- **Almacenamiento:** Persistencia en [[PostgreSQL]].
- Envía información procesada al sistema de [[Rastreo Bovino]]."""
    },
    {
        "id": "listener-telemetria",
        "title": "Listener Telemetria",
        "source": "vault",
        "tags": ["soap", "xml", "go", "gps"],
        "content": """Servicio en [[Go]] que recibe peticiones SOAP XML con datos de telemetría de sensores GPS.

- **Protocolo:** HTTP/HTTPS concurrente con parsing SOAP XML.
- **Transformación:** Convierte sensores a JSON estructurado y guarda en [[PostgreSQL]].
- Alimenta los datos de telemetría para [[Rastreo Bovino]] y [[GEOTASK]]."""
    },
    {
        "id": "hello-crea-mundo",
        "title": "Hello Crea Mundo",
        "source": "vault",
        "tags": ["patentes", "chile", "react", "express"],
        "content": """Sistema de Búsqueda de Patentes de vehículos chilenos (APS).

- **Frontend:** [[React]] + TypeScript + [[Vite]].
- **Backend:** [[Express]] + [[PostgreSQL]] (`aps.pregps.cl`).
- **Propósito:** Consulta de información vehicular y administración de usuarios."""
    },
    {
        "id": "supramemory",
        "title": "Supramemory",
        "source": "vault",
        "tags": ["ai", "knowledge-graph", "python", "fastapi"],
        "content": """Personal Knowledge Graph multi-origen e interfaz estilo [[Red Neuronal]].

- **Stack:** [[Python]], [[FastAPI]], [[SQLite FTS5]], D3.js v7.
- **Propósito:** Almacena notas y memoria viva para [[Agentes IA]] e integra todo el [[Ecosistema Desarrollos]].
- **Despliegue:** Contenedorizado en [[Docker & Dokploy]]."""
    },
    {
        "id": "postgresql",
        "title": "PostgreSQL",
        "source": "vault",
        "tags": ["database", "sql", "infrastructure"],
        "content": """Base de datos relacional principal utilizada en el ecosistema.

- Base de datos de [[GeotaskAPI]].
- Almacenamiento de telemetría para [[SST310U Listener]] y [[Listener Telemetria]].
- Base de datos vehicular en [[Hello Crea Mundo]]."""
    },
    {
        "id": "go-lang",
        "title": "Go Language",
        "source": "vault",
        "tags": ["language", "backend", "tcp"],
        "content": """Lenguaje concurrente de alto rendimiento utilizado para servicios de red e IoT:

- [[SST310U Listener]]: Servidor TCP satelital.
- [[Listener Telemetria]]: Receptor SOAP XML de telemetría GPS."""
    },
    {
        "id": "react-framework",
        "title": "React",
        "source": "vault",
        "tags": ["frontend", "javascript", "UI"],
        "content": """Librería UI estándar para aplicaciones web y móviles:

- [[GeotaskWEB]] & [[GeotaskMobile]]
- [[Rastreo Bovino]]
- [[Hello Crea Mundo]]"""
    },
    {
        "id": "agentes-ia",
        "title": "Agentes IA",
        "source": "vault",
        "tags": ["ai", "llm", "prompt"],
        "content": """Sistemas inteligentes autónomos impulsados por LLMs y [[Vercel AI SDK]].

- Operan en [[GeoIA]] para atención a clientes.
- Consumen contexto y guardan aprendizajes en [[Supramemory]]."""
    },
    {
        "id": "docker-dokploy",
        "title": "Docker & Dokploy",
        "source": "vault",
        "tags": ["deploy", "devops", "docker"],
        "content": """Infraestructura de despliegue y contenedorización en la nube.

- Servidor VPS con [[Docker]] y orquestación en Dokploy.
- Despliegue de [[Supramemory]], [[GEOTASK]] y gateways de [[GeoIA]]."""
    }
]

print(f"Seeding {len(notes)} project notes to {API_URL}...")
for n in notes:
    data = json.dumps(n).encode('utf-8')
    req = urllib.request.Request(
        f"{API_URL}/notes",
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"  [OK {resp.status}] {n['title']}")
    except Exception as e:
        print(f"  [ERR] {n['title']}: {e}")

print("Seeding completed successfully!")
