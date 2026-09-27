# -*- coding: utf-8 -*-
import json
import time
import urllib.request
import urllib.error

TOKEN = 'sk-qJgoDtWOgtjv1JKNaP_9VRHm98dsdtefXy52WTO047c'
BASE_URL = 'https://supramemory.grupogeo.cl'

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

NOTES = [
    {
        'id': 'mapa-general-desarrollos-grupogeo',
        'title': 'Mapa General de Desarrollos GrupoGeo',
        'tags': ['hub', 'grupogeo', 'arquitectura', 'desarrollos'],
        'source': 'agent',
        'content': '''# Mapa General de Desarrollos GrupoGeo

> [!NOTE]
> Hub maestro de memoria neural para **GrupoGeo**. Este nodo central interconecta todos los proyectos, plataformas de software, modelos de IA e infraestructura mantenidos por el equipo en el directorio `Desarollo`.

---

## 🗺️ Ecosistema de Proyectos

```
                     ┌─────────────────────────────────────────┐
                     │   MAPA GENERAL DESARROLLOS GRUPOGEO     │
                     └────────────────────┬────────────────────┘
                                          │
       ┌──────────────────┬───────────────┼───────────────┬──────────────────┐
       ▼                  ▼               ▼               ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────┐   ┌──────────────┐
│  [[GeoJobs]] │   │  [[Geotask]] │   │ [[OpenclawSEC]]│  │  [[TotemIA]] │   │[[GrupoGeo-Web]]│
└──────┬───────┘   └──────┬───────┘   └───────────────┘   └──────────────┘   └──────────────┘
       │                  │
       │           ┌──────┴────────────────────────┐
       │           ▼                               ▼
       │   [[Geotask-Accesos-y-Entornos]]   [[Credenciales-y-Accesos-Maestros]]
       │                                                   ▲
       └───────────────────────────────────────────────────┤
                                                           │
                                                   [[Supramemory]]
                                                           ▲
                                                           │
                                       [[Rutinas-de-Mantenimiento-Supramemory]]
```

---

## 📂 Directorio de Proyectos

### 1. [[GeoJobs]]
- **Propósito:** Plataforma dual (App Móvil + Web Empresas) para emparejamiento laboral hiper-local basado en tiempo de traslado y geovallas concéntricas (1 a 5).
- **Stack:** React Native / Expo, Next.js 14, Node.js / NestJS, PostGIS.
- **Estado:** Especificaciones completas, Roadmap JIRA y builds APK v0.2.0 a v1.0.0.

### 2. [[Geotask]]
- **Propósito:** Plataforma empresarial multi-tenant de gestión de tareas y cuadrillas en terreno con formularios dinámicos y sincronización offline-first.
- **Estructura Monorepo:**
  - `GeotaskAPI`: Backend Node.js, Express, Prisma (PostgreSQL schema `taskmanager`), JWT.
  - `GeotaskWEB`: Panel web administrativo en React 19, Vite 7, Tailwind 4.
  - `GeotaskMobile`: Aplicación de campo en React Native 0.74, Expo 51, SQLite local queue.
- **Detalle de Entornos y Claves:** Ver [[Geotask-Accesos-y-Entornos]].

### 3. [[OpenclawSEC]]
- **Propósito:** Arquitectura de seguridad en 3 capas (Inbound Validator, Core Orchestrator y Outbound DLP Validator) para pasarelas de agentes de Inteligencia Artificial sin fricción de acceso.
- **Stack:** TypeScript, Node.js (ESM), Oxlint, Vitest, Docker, Fly.io, Render.

### 4. [[TotemIA]]
- **Propósito:** Asistente conversacional de alta velocidad para kioscos y tótems presenciales con inferencia local en tiempo real.
- **Stack:** Fine-Tuning LoRA / SFT sobre `Qwen/Qwen2.5-7B-Instruct` optimizado para GPU NVIDIA RTX 4050 (6GB VRAM), exportado a formato GGUF para ejecución con `llama.cpp` nativo.

### 5. [[GrupoGeo-Web]]
- **Propósito:** Portal corporativo oficial de GrupoGeo para comercialización de Geotask y Geotracker, captura de prospectos comerciales y formulario con despacho SMTP seguro.
- **Stack:** HTML5 semántico, CSS responsivo, PHP nativo con socket SSL Hostinger (`smtp.hostinger.com:465`).

### 6. [[Supramemory]]
- **Propósito:** Memoria neural viva y base de conocimiento para agentes de IA (Antigravity).
- **URL Producción:** `https://supramemory.grupogeo.cl` (Dockploy).
- **Stack:** FastAPI, SQLite WAL, D3 Force Graph, Búsqueda Vectorial, Vault Markdown Obsidian.

---

## 🔐 Bóveda y Rutinas
- **Credenciales Maestras:** Ver [[Credenciales-y-Accesos-Maestros]].
- **Protocolo de Operación:** Ver [[Rutinas-de-Mantenimiento-Supramemory]].
'''
    },
    {
        'id': 'geojobs',
        'title': 'GeoJobs — Plataforma de Empleo por Hiper-Proximidad',
        'tags': ['geojobs', 'proyecto', 'postgis', 'mobile', 'empleo'],
        'source': 'agent',
        'content': '''# GeoJobs — Plataforma de Empleo por Hiper-Proximidad

> [!NOTE]
> **GeoJobs** es una plataforma tecnológica dual diseñada para revolucionar la contratación en el sector operativo, técnico e inicial mediante el **match por hiper-proximidad geográfica** entre la vivienda del colaborador y la sucursal de la empresa.

---

## 🎯 Propuesta de Valor y Beneficios
- **Titular Hero:** *"Contrata a personas que viven a minutos del domicilio de tu empresa"*.
- **Los 8 Beneficios Clave:**
  1. Menor rotación laboral (mayor estabilidad).
  2. Menor gasto en transporte y combustible para el empleado.
  3. Reducción drástica del estrés y licencias médicas.
  4. Mayor sentido de pertenencia y apego a la empresa.
  5. Mayor calidad de vida (posibilidad de almorzar en casa).
  6. Ahorro de 2 a 4 horas diarias de viaje en congestión.
  7. Puntualidad garantizada sin contingencias viales.
  8. Lealtad y fidelización a largo plazo.

---

## 🏗️ Arquitectura Técnica

### 1. App Móvil (Trabajadores / Postulantes)
- **Tecnología:** React Native con Expo 51+ / TypeScript.
- **Funcionalidades:**
  - Registro ágil y validación de identidad (RUT chileno / OTP).
  - Georreferenciación precisa del hogar (Google Places + ajuste de pin en mapa).
  - Perfil curricular estructurado por competencias y experiencia.
  - Recepción de ofertas geolocalizadas con cálculo de tiempo de traslado.
  - Postulación express de 1 solo toque.
- **Compilaciones Disponibles en Local (`C:/Users/mik10/Desarollo/GeoJobs`):**
  - `GeoJobs-v1.0.0.apk` (Versión estable release)
  - `GeoJobs-v0.2.2.apk`, `GeoJobs-v0.2.1.apk`, `GeoJobs-v0.2.0.apk`

### 2. Plataforma Web (Empresas Contratantes)
- **Tecnología:** Next.js 14 / Tailwind CSS / Mapbox GL JS.
- **Funcionalidades:**
  - Visualizador geográfico de candidatos anónimos mediante círculos concéntricos.
  - Matriz de cálculo de precio dinámico por geovalla (Geovallas 1 a 5).
  - Cesta de compra de currículums (desbloqueo de datos de contacto de candidatos cercanos).

### 3. Backend & Base de Datos
- **Tecnología:** Node.js / NestJS con TypeScript.
- **Base de Datos:** PostgreSQL con extensión espacial **PostGIS** para cálculo de distancias geodésicas y polígonos de geovalla.
- **Cálculo de Rutas:** Integración con OSRM y Google Distance Matrix API.

---

## 📊 Hoja de Ruta (Plan JIRA de 4 Fases)
Documentado en `GeoJobs_JIRA_Plan.csv`:
- **Fase 1 (Semanas 1-2):** Scaffolding, repositorios, Docker y CI/CD.
- **Fase 2 (Semanas 3-6):** Backend Core, modelo PostGIS, motor de matching multicriterio (50% proximidad, 30% skills, 20% experiencia).
- **Fase 3 (Semanas 7-10):** App móvil, registro, georreferenciación y notificaciones push.
- **Fase 4 (Semanas 7-10):** Plataforma web empresas, geovallas interactivas y pasarela de pago.

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Credenciales-y-Accesos-Maestros]]
'''
    },
    {
        'id': 'geotask',
        'title': 'Geotask — Gestión Multi-Tenant de Tareas en Terreno',
        'tags': ['geotask', 'proyecto', 'offline-first', 'multitenant', 'prisma', 'react'],
        'source': 'agent',
        'content': '''# Geotask — Gestión Multi-Tenant de Tareas en Terreno

> [!IMPORTANT]
> **Geotask** es la plataforma insigne de GrupoGeo para la orquestación, despacho, seguimiento y certificación de cuadrillas operativas en terreno mediante formularios dinámicos y arquitectura **offline-first**.

---

## 🧱 Estructura Monorepo (3 Subproyectos Independientes)

El directorio `C:/Users/mik10/Desarollo/Geotask` se organiza en tres proyectos autónomos con sus propios despliegues:

```
┌────────────────────────────────────────────────────────────────────────┐
│                          GEOTASK MONOREPO                              │
├─────────────────────┬──────────────────────┬───────────────────────────┤
│    GeotaskAPI       │     GeotaskWEB       │      GeotaskMobile        │
│  Backend / REST API │  Panel Admin Web     │  App Operadores Terreno   │
│  Node.js ESM + JWT  │  React 19 + Vite 7   │  React Native + Expo 51   │
│  Prisma (Postgres)  │  Tailwind 4 + Axios  │  SQLite Offline-First     │
└─────────────────────┴──────────────────────┴───────────────────────────┘
```

### 1. `GeotaskAPI` (Backend)
- **Repositorio:** `https://github.com/MikelCuellar/GeotaskAPI.git`
- **Puerto y Ejecución:** Puerto `3030`. `npm run dev` (hot-reload), `npm start` (producción).
- **Arquitectura:** Patrón `routes -> controllers -> Prisma` (sin capa intermedia innecesaria).
- **Prisma MultiSchema:** Todo el modelo de datos reside en el esquema PostgreSQL `taskmanager`.
- **Seguridad:** Middleware de autenticación JWT, bcrypt con política de historial de contraseñas (`HistorialPassword`), validación de RUT chileno, rate-limiting en `/api/auth/login`, subida de adjuntos multer hacia `public/assets`.
- **Roles:**
  1. `Super Usuario` (acceso global multi-empresa)
  2. `Admin Empresa` (gestión total de su empresa tenant)
  3. `Admin Grupo` (gestión de cuadrillas o sucursales)
  4. `Usuario App Movil` (ejecutor de terreno)

### 2. `GeotaskWEB` (Panel Administrativo)
- **Repositorio:** `https://github.com/MikelCuellar/GeotaskWEB.git`
- **Puerto:** `5173` en desarrollo local.
- **Características:** Single Page Application modular (`src/pages/*`), constructor visual de formularios dinámicos (`FormBuilder.jsx`, `DynamicForm.jsx`), mapas satelitales Google Maps, gestión de clientes, catálogos e inventarios.

### 3. `GeotaskMobile` (App Móvil Offline-First)
- **Repositorio:** `https://github.com/MikelCuellar/GeotaskMobile.git`
- **Paquete Android:** `com.aiep.geotask`
- **Patrón Offline-First:**
  - Base de datos local SQLite con tabla `offline_mutation_queue`.
  - Cuando se pierde la señal de red en terreno, los formularios, fotos y firmas se almacenan localmente.
  - Al recuperar conectividad, `SyncService` despacha las mutaciones en estricto orden FIFO:
    `Subir fotos/archivos -> Obtener URLs remotas -> Reemplazar en payload -> PUT Tarea completada`.

---

## 🔗 Enlaces Relacionados
- [[Geotask-Accesos-y-Entornos]] — Base de datos, API Keys y credenciales técnicas.
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Credenciales-y-Accesos-Maestros]]
'''
    },
    {
        'id': 'geotask-accesos-y-entornos',
        'title': 'Geotask — Accesos, Endpoints y Entornos',
        'tags': ['geotask', 'credenciales', 'accesos', 'db', 'endpoints'],
        'source': 'agent',
        'content': '''# Geotask — Accesos, Endpoints y Entornos

> [!CAUTION]
> Información confidencial de infraestructura y conexiones de bases de datos para Geotask. Mantener protegido.

---

## 🗄️ Bases de Datos PostgreSQL

| Entorno | Host / IP | Puerto | Base de Datos | Schema | Usuario | Contraseña |
|---|---|---|---|---|---|---|
| **Desarrollo (DEV)** | `195.200.7.102` | `5432` | `geotask` | `taskmanager` | `rootgeo` | `vbz4yhr.WER1jhz9kyk` |
| **Producción (PROD)** | `187.77.201.30` | `5432` | `geotask` | `taskmanager` | `rootgeo` | `vbz4yhr.WER1jhz9kyk` |

### Cadenas de Conexión (Prisma / URI)
- **DEV:**
  ```text
  postgresql://rootgeo:vbz4yhr.WER1jhz9kyk@195.200.7.102:5432/geotask?schema=taskmanager
  ```
- **PROD:**
  ```text
  postgresql://rootgeo:vbz4yhr.WER1jhz9kyk@187.77.201.30:5432/geotask?schema=taskmanager
  ```

---

## 🌐 URLs y Endpoints de API

- **API Producción:** `https://api.geotask.cl/api` y `https://api.quietgps.cl/api`
- **API Desarrollo:** `https://apidev.geotask.cl/api`
- **Puerto Local API:** `3030` (`http://localhost:3030/api`)
- **Panel Web Producción:** `https://geotask.cl` y `https://geotask.quietgps.cl`
- **Panel Web Desarrollo:** `https://dev.geotask.cl`

---

## 🔑 Llaves de API y Servicios Externos

### Google Maps API Keys
- **Panel Web (`GeotaskWEB/.env`):**
  `AIzaSyC7bksanZ54FtrJsKKw6HHIEO13eA7BsVY`
- **App Móvil (`GeotaskMobile/.env`):**
  `AIzaSyA-KxWHvYvQxAh-6DrEFh9iN_b5sGZ28v0`

### Expo Push Notifications
- **Project ID:** `52f27fac-05e6-46fb-92bd-9b09f88a5664`
- **Android Package:** `com.aiep.geotask`

### JWT Secret (`GeotaskAPI`)
- `946d2cf9e3d04c99866b4d7eecb9c5bb7a0d96766390550773f0630b8c84bfbfb3742ce883f0cba92f32142b0434793612c12226f593c3b6f95b201083409725`

---

## 🔗 Enlaces Relacionados
- [[Geotask]]
- [[Credenciales-y-Accesos-Maestros]]
- [[Mapa-General-Desarrollos-GrupoGeo]]
'''
    },
    {
        'id': 'openclawsec',
        'title': 'OpenclawSEC — Seguridad y Hardening Multi-Agente',
        'tags': ['openclaw', 'seguridad', 'agentes-ia', 'dlp', 'gateway'],
        'source': 'agent',
        'content': '''# OpenclawSEC — Seguridad y Hardening Multi-Agente

> [!NOTE]
> **OpenclawSEC** implementa un modelo de seguridad por capas en el gateway de OpenClaw con el objetivo de gobernar interacciones de IA, evitar accesos no autorizados y prevenir la fuga de datos confidenciales (DLP) hacia modelos de lenguaje externos.

---

## 🛡️ Arquitectura de 3 Agentes de Seguridad

```
Remitente (Usuario / Bot)
           │
           ▼
┌───────────────────────────────────────┐
│     AGENTE 1: INBOUND VALIDATOR       │  Valida permisos de interacción, origen,
│     `validateInboundInteraction`      │  identidad y políticas de contexto previo.
└──────────────────┬────────────────────┘
                   │  (Permitido)
                   ▼
┌───────────────────────────────────────┐
│     AGENTE 2: CORE ORCHESTRATOR       │  Bucle de ejecución nativo (`AgentLoop`)
│         OpenClaw Runtime              │  sin alteraciones invasivas en el motor.
└──────────────────┬────────────────────┘
                   │  (Respuesta bruta)
                   ▼
┌───────────────────────────────────────┐
│    AGENTE 3: OUTBOUND DLP VALIDATOR   │  Inspección profunda de contenido saliente;
│      `validateOutboundResponse`       │  censura llaves, datos personales o bloquea.
└──────────────────┬────────────────────┘
                   │
                   ▼
Respuesta Segura al Canal (Slack, Discord, WhatsApp, etc.)
```

---

## 💻 Detalles de Implementación
- **Archivo de Validadores:** `src/security/validators.ts`.
- **Estrategia Inbound:** Validación contra lista blanca institucional y evaluación semántica previa de la intención del usuario.
- **Estrategia Outbound (DLP):** Búsqueda de patrones Regex de credenciales (API keys, cadenas de conexión, passwords, tokens `sk-...`) y censura en tiempo real antes de emitir el mensaje al usuario final.

---

## 📦 Información de Repositorio y Despliegue
- **Repositorio:** `https://github.com/openclaw/openclaw.git`
- **Herramientas de Calidad:** `oxlint` (linter ultrarrápido), `vitest` (pruebas unitarias), `pnpm` workspaces.
- **Despliegue:** Soporte para contenedores `Dockerfile`, `docker-compose.yml`, `fly.toml` (Fly.io) y `render.yaml` (Render).

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Supramemory]]
'''
    },
    {
        'id': 'totemia',
        'title': 'TotemIA — Kiosco Inteligente y Fine-Tuning LLM Local',
        'tags': ['totemia', 'llm', 'lora', 'rtx4050', 'gguf', 'llamacpp', 'ia-local'],
        'source': 'agent',
        'content': '''# TotemIA — Kiosco Inteligente y Fine-Tuning LLM Local

> [!TIP]
> **TotemIA** es un sistema conversacional de hardware local para tótems y módulos de atención presencial, capaz de responder de forma inmediata mediante un modelo de lenguaje de 7B parámetros adaptado mediante LoRA y cuantizado para inferencia en CPU/GPU sin conexión a internet.

---

## ⚙️ Especificaciones de Fine-Tuning (`soup.yaml`)

- **Modelo Base:** `Qwen/Qwen2.5-7B-Instruct`
- **Tarea:** SFT (Supervised Fine-Tuning)
- **Formato de Entrenamiento:** ChatML
- **Dataset:** `./data/totem_v2_train.jsonl` (95% entrenamiento, 5% validación)
- **Restricción de Hardware:** Optimizado para tarjeta gráfica de laptop **NVIDIA GeForce RTX 4050 (6GB VRAM)**.

### Hiperparámetros de Memoria Crítica
- `stream_layers: true` — Técnica indispensable para poder entrenar un modelo de 7B en sólo 6GB de VRAM.
- `quantization: 4bit` (NF4)
- `batch_size: 1`
- `max_length: 768` tokens
- `gradient_checkpointing: true`
- `lr: 2e-4`
- `epochs: 3`

### Parámetros LoRA
- `r: 32`
- `alpha: 64`
- `dropout: 0.05`
- `target_modules`: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.

---

## 🚀 Pipeline de Despliegue e Inferencia

1. **Fusión de Pesos:** `merge_directo.py` fusiona los adaptadores LoRA generados en `./output` con el modelo base sin dependencias de Soup.
2. **Conversión GGUF:** `convertir_gguf.py` exporta los pesos al formato GGUF compatible con llama.cpp.
3. **Ejecución Local:** Binarios de `llama.cpp` incluidos en `llama-bin/` para inferencia local a alta velocidad sin consumo de APIs comerciales.

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Credenciales-y-Accesos-Maestros]]
'''
    },
    {
        'id': 'grupogeo-web',
        'title': 'GrupoGeo Web — Portal Institucional y Captura de Leads',
        'tags': ['grupogeo', 'web', 'smtp', 'hostinger', 'leads'],
        'source': 'agent',
        'content': '''# GrupoGeo Web — Portal Institucional y Captura de Leads

> [!NOTE]
> Portal web de cara al público de **GrupoGeo** (`grupogeo.cl`). Diseñado para presentar el catálogo de productos y canalizar solicitudes comerciales directamente hacia el equipo de ventas.

---

## 📬 Configuración SMTP del Formulario de Contacto

El archivo `enviar-correo.php` implementa un cliente socket SSL nativo para garantizar el envío confiable de leads sin caer en carpetas de SPAM:

- **Servidor SMTP:** `smtp.hostinger.com`
- **Puerto:** `465` (SSL)
- **Usuario Remitente:** `contacto@grupogeo.cl`
- **Contraseña SMTP:** `APG8a4l/`
- **Destino de Notificaciones:** `contacto@grupogeo.cl`
- **Asunto Predeterminado:** `"Nuevo Lead desde Sitio Web - GrupoGeo"`

---

## 💻 Repositorio y Páginas del Sitio
- **Repositorio Oficial:** `https://github.com/MikelCuellar/grupogeo-web.git`
- **Rama Principal:** `main`
- **Páginas Principales:**
  - `index.html`: Portada institucional, propuesta de valor de GrupoGeo.
  - `geotask-details.html`: Ficha comercial detallada de la plataforma Geotask.
  - `geotracker-details.html`: Ficha comercial detallada de la plataforma Geotracker (rastreo y telemetría GPS).

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Credenciales-y-Accesos-Maestros]]
'''
    },
    {
        'id': 'supramemory',
        'title': 'Supramemory — Cerebro Neural de Conocimiento para Agentes',
        'tags': ['supramemory', 'memoria', 'cerebro', 'agentes-ia', 'dockploy'],
        'source': 'agent',
        'content': '''# Supramemory — Cerebro Neural de Conocimiento para Agentes

> [!IMPORTANT]
> **Supramemory** es el cerebro central de memoria persistente para el ecosistema de GrupoGeo y los agentes autónomos de IA. Proporciona almacenamiento de notas en Markdown tipo Obsidian, grafos de conocimiento interactivos y APIs seguras.

---

## 🌐 Instancia de Producción
- **URL Base:** `https://supramemory.grupogeo.cl`
- **Plataforma de Despliegue:** Dockploy (servidor Docker cloud).
- **Repositorio GitHub:** `https://github.com/MikelCuellar/supramemory`
- **Token Maestro del Agente:** `sk-qJgoDtWOgtjv1JKNaP_9VRHm98dsdtefXy52WTO047c`
  - Tipo: Bearer Token
  - Scopes: `read`, `write`, `admin`

---

## 🧠 Características Principales

1. **Vault Markdown Obsidian:**
   - Notas organizadas jerárquicamente en árbol de carpetas.
   - Soporte nativo para wikilinks `[[Nombre Nota]]`, etiquetas `#tag` y callouts `> [!NOTE]`.
2. **Safe Rename Bidireccional:**
   - Al renombrar una nota mediante `/notes/rename`, Supramemory rastrea y reescribe automáticamente todas las referencias `[[...]]` en todo el vault.
3. **Grafo Neural con D3.js:**
   - Modo Global: Mapa de red completo con código de colores según el origen de la nota.
   - Modo Local: Vista de subgrafo centrado en una nota específica con profundidad ajustable (1 a 4 saltos).
   - Ajustes de física en vivo (repulsión, distancia de aristas, nodos huérfanos).
4. **Búsqueda Híbrida y RAG:**
   - Búsqueda textual y vectorial con embeddings semánticos para alimentar el contexto de los agentes de IA.
5. **Internacionalización Completa:**
   - Interfaz y documentación disponibles en Español (Neutro/México), English, Français y Svenska.

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Credenciales-y-Accesos-Maestros]]
- [[Rutinas-de-Mantenimiento-Supramemory]]
'''
    },
    {
        'id': 'credenciales-y-accesos-maestros',
        'title': 'Bóveda de Credenciales, Llaves y Accesos Maestros',
        'tags': ['credenciales', 'seguridad', 'accesos', 'boveda', 'keys'],
        'source': 'agent',
        'content': '''# Bóveda de Credenciales, Llaves y Accesos Maestros

> [!CAUTION]
> Bóveda consolidada de credenciales, tokens, contraseñas de bases de datos y llaves de API para todos los desarrollos de GrupoGeo.

---

## 1. Supramemory (Cerebro Neural)
- **URL:** `https://supramemory.grupogeo.cl`
- **Token Bearer Agente:** `sk-qJgoDtWOgtjv1JKNaP_9VRHm98dsdtefXy52WTO047c`
- **Permisos:** `read,write,admin`
- **Repo:** `https://github.com/MikelCuellar/supramemory`

---

## 2. Geotask (Bases de Datos y APIs)
- **Base de Datos PostgreSQL DEV:**
  - Host: `195.200.7.102` | Puerto: `5432`
  - Usuario: `rootgeo` | Password: `vbz4yhr.WER1jhz9kyk`
  - Base: `geotask` | Schema: `taskmanager`
  - URI: `postgresql://rootgeo:vbz4yhr.WER1jhz9kyk@195.200.7.102:5432/geotask?schema=taskmanager`
- **Base de Datos PostgreSQL PROD:**
  - Host: `187.77.201.30` | Puerto: `5432`
  - Usuario: `rootgeo` | Password: `vbz4yhr.WER1jhz9kyk`
  - Base: `geotask` | Schema: `taskmanager`
  - URI: `postgresql://rootgeo:vbz4yhr.WER1jhz9kyk@187.77.201.30:5432/geotask?schema=taskmanager`
- **JWT Secret:** `946d2cf9e3d04c99866b4d7eecb9c5bb7a0d96766390550773f0630b8c84bfbfb3742ce883f0cba92f32142b0434793612c12226f593c3b6f95b201083409725`
- **Google Maps API Key Web:** `AIzaSyC7bksanZ54FtrJsKKw6HHIEO13eA7BsVY`
- **Google Maps API Key Mobile:** `AIzaSyA-KxWHvYvQxAh-6DrEFh9iN_b5sGZ28v0`
- **Expo Push Project ID:** `52f27fac-05e6-46fb-92bd-9b09f88a5664`
- **Dominios:** `https://geotask.cl`, `https://geotask.quietgps.cl`, `https://apidev.geotask.cl`

---

## 3. GrupoGeo Web (Correo SMTP)
- **Servidor SMTP:** `smtp.hostinger.com` (puerto 465 SSL)
- **Usuario:** `contacto@grupogeo.cl`
- **Contraseña:** `APG8a4l/`
- **Repo:** `https://github.com/MikelCuellar/grupogeo-web.git`

---

## 4. Repositorios de Código Fuente (GitHub)
- **GeotaskAPI:** `https://github.com/MikelCuellar/GeotaskAPI.git`
- **GeotaskWEB:** `https://github.com/MikelCuellar/GeotaskWEB.git`
- **GeotaskMobile:** `https://github.com/MikelCuellar/GeotaskMobile.git`
- **GrupoGeo Web:** `https://github.com/MikelCuellar/grupogeo-web.git`
- **Supramemory:** `https://github.com/MikelCuellar/supramemory.git`
- **OpenclawSEC:** `https://github.com/openclaw/openclaw.git`

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Geotask-Accesos-y-Entornos]]
- [[Supramemory]]
'''
    },
    {
        'id': 'rutinas-de-mantenimiento-supramemory',
        'title': 'Rutinas y Protocolo de Memoria para Antigravity',
        'tags': ['rutinas', 'antigravity', 'protocolo', 'memoria-viva'],
        'source': 'agent',
        'content': '''# Rutinas y Protocolo de Memoria para Antigravity

> [!IMPORTANT]
> Este documento establece el **Protocolo Operativo de Memoria Viva** que Antigravity debe seguir en todas sus sesiones de desarrollo dentro de `C:/Users/mik10/Desarollo`.

---

## 🔄 Protocolo de Memoria en 3 Pasos

```
   ┌────────────────────────────────────────────────────────┐
   │             PASO 1: CONSULTA DE INICIO                 │
   │  Antes de programar, consultar Supramemory para traer   │
   │  credenciales, arquitectura y lecciones aprendidas.    │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │             PASO 2: EJECUCIÓN Y TRABAJO                │
   │  Programación, refactorización y solución de tareas.   │
   └───────────────────────────┬────────────────────────────┘
                               │
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │             PASO 3: REGISTRO DE CIERRE                 │
   │  Actualizar Supramemory con nuevas decisiones, claves, │
   │  bugs resueltos y enlaces bidireccionales.             │
   └────────────────────────────────────────────────────────┘
```

---

## 📋 Reglas de Documentación para Antigravity

1. **Enlace Bidireccional Obligatorio:**
   - Toda nueva nota debe enlazar al menos a [[Mapa-General-Desarrollos-GrupoGeo]] o al nodo de su proyecto correspondiente (`[[GeoJobs]]`, `[[Geotask]]`, `[[OpenclawSEC]]`, `[[TotemIA]]`, `[[GrupoGeo-Web]]`).
2. **Formato Obsidian Estricto:**
   - Títulos claros en `# H1`.
   - Callouts estándar de GitHub/Obsidian (`> [!NOTE]`, `> [!IMPORTANT]`, `> [!TIP]`, `> [!WARNING]`, `> [!CAUTION]`).
   - Etiquetas semánticas `#tema` en minúsculas.
3. **Preservación de Credenciales:**
   - Cualquier cambio en contraseñas de base de datos, puertos o tokens de API debe actualizarse inmediatamente en [[Credenciales-y-Accesos-Maestros]].
4. **Uso de la Herramienta Local:**
   - Antigravity utilizará el script `.agents/skills/supramemory/supramemory_client.py` o solicitudes directas a `https://supramemory.grupogeo.cl` con el Bearer token preconfigurado.

---

## 🔗 Enlaces Relacionados
- [[Mapa-General-Desarrollos-GrupoGeo]]
- [[Supramemory]]
- [[Credenciales-y-Accesos-Maestros]]
'''
    }
]

def upload_all():
    print(f'Comenzando subida de {len(NOTES)} notas maestras a {BASE_URL}...')
    for n in NOTES:
        payload = {
            'id': n['id'],
            'title': n['title'],
            'content': n['content'],
            'source': n['source'],
            'tags': n['tags']
        }
        data_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            f'{BASE_URL}/notes',
            data=data_bytes,
            headers=HEADERS,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f'✅ Creada: {n["title"]} (HTTP {resp.status})')
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            print(f'⚠️ Error en {n["title"]}: HTTP {e.code} - {err_body}')
        except Exception as e:
            print(f'❌ Excepción en {n["title"]}: {e}')
        time.sleep(0.3)
    print('🚀 ¡Sincronización completa!')

if __name__ == '__main__':
    upload_all()
