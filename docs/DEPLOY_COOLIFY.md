# Deploy en Coolify

Coolify detecta `docker-compose.yml` automáticamente. Esta guía asume que ya tenés Coolify funcionando en tu VPS Hostinger (31.97.92.253).

## Pre-requisitos

1. Repo en GitHub: `https://github.com/MikelCuellar/supramemory.git`
2. Dominio `supramemory.grupogeo.cl` apuntando a tu VPS (registro A o CNAME según config DNS de GrupoGeo)
3. Coolify accesible en tu VPS

## Pasos

### 1. Generar API_KEY segura

En tu máquina local:
```bash
openssl rand -hex 32
# Output: 5f4dcc3b5aa765d1ef8e1d2... (64 chars)
```

Anotala — la vas a pegar en Coolify como variable de entorno.

### 2. Crear app en Coolify

1. Login en Coolify
2. **+ New Resource** → **Docker Compose**
3. **Source**: pegá `https://github.com/MikelCuellar/supramemory.git` (o seleccioná tu org)
4. **Branch**: main
6. **Build Pack**: Docker Compose
7. Click **Deploy**

### 3. Variables de entorno

En Coolify → tu app → **Environment Variables**, agregá:

| Variable          | Value                                                    |
| ----------------- | -------------------------------------------------------- |
| `API_KEY`         | el hash generado en paso 1                              |
| `PORT`            | `8000`                                                   |
| `LOG_LEVEL`       | `info`                                                   |
| `CORS_ORIGINS`    | `https://supramemory.grupogeo.cl` (NO uses `*` en prod)  |

### 4. Volúmenes (persistentes)

Coolify monta los volúmenes del `docker-compose.yml` automáticamente:

- `./data/vault` → persistente en host, donde están tus `.md`
- `./data/db` → persistente, donde está el SQLite

**Importante:** los volúmenes persisten entre deploys. Coolify te muestra la ruta exacta en el panel (ej: `/var/lib/docker/volumes/...`).

### 5. Dominio + HTTPS

1. En Coolify → tu app → **Domains**
2. Agregá `supramemory.grupogeo.cl`
3. Coolify configura Traefik con Let's Encrypt automático
4. Esperá 1-2 minutos a que el certificado se emita

### 6. Verificación

```bash
# Health check (sin auth)
curl https://supramemory.grupogeo.cl/health

# Esperado:
# {"status":"ok","version":"0.1.0","notes_count":0,"links_count":0}

# Con auth
curl -H "Authorization: Bearer $API_KEY" \
  https://supramemory.grupogeo.cl/notes
```

### 7. Agregar notas

Tres caminos:

**a) Subir archivos `.md` directamente al volumen del VPS:**
```bash
# En tu máquina local
scp mi-nota.md root@31.97.92.253:/ruta/al/volumen/data/vault/

# O vía Coolify: Server → tu-app → Volumes → Browse Files → Upload
```

**c) Vía API:**
```bash
curl -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Mi nota","content":"...","tags":["test"]}' \
  https://supramemory.grupogeo.cl/notes
```

Después de subir archivos, llamá:
```bash
curl -X POST -H "Authorization: Bearer $API_KEY" \
  https://supramemory.grupogeo.cl/ingest/vault
```

### 8. Logs y debugging

Coolify → tu app → **Logs** muestra stdout/stderr en tiempo real.

Para problemas comunes:
- **API key inválida**: revisá que la env var esté bien en Coolify
- **Vault no sincroniza**: revisá que el path `/vault` tenga permisos de lectura
- **CORS**: si accedés desde otro dominio, actualizá `CORS_ORIGINS`

## CI/CD (auto-deploy en push)

Si querés que Coolify redespliegue automáticamente en cada `git push` a main:

1. Coolify → tu app → **Webhooks** → copiá el webhook URL
2. GitHub → tu repo → **Settings** → **Webhooks** → **Add webhook`
3. Pegá el URL, content-type `application/json`, evento `push`

Listo. Cada push a `main` redespliega automáticamente.

## Backup

El volumen `data/db` contiene todo el grafo. Backup simple:

```bash
# En VPS
cp /var/lib/docker/volumes/supramemory_data_db/_data/supramemory.db \
   /backup/supramemory-$(date +%Y%m%d).db
```

El volumen `data/vault` contiene tus `.md` originales, así que con tener los `.md` respaldados (git, sync, lo que sea) ya podés reconstruir el SQLite con `POST /ingest/vault`.