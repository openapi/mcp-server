# Environment: Docker / Docker Compose

Run the server as a container with a local volume for storage. Suitable for
single-machine deployments, local testing with Docker, and as the base for
more complex orchestration setups.

---

## Minimum `compose.yml`

```yaml
services:
  mcp:
    image: ghcr.io/openapi/mcp-server:latest
    # or build locally:
    # build:
    #   context: .
    #   dockerfile: docker/latest/Dockerfile
    ports:
      - "8080:8080"
    environment:
      PORT: "8080"
      BASE_URL: "http://localhost:8080"
      SERVICES_CREDENTIALS: "{}"
      STORAGE_BACKEND: "local"
      STORAGE_PATH: "/app/openapi_storage"
    volumes:
      - openapi_storage:/app/openapi_storage

volumes:
  openapi_storage:
```

Start:

```bash
docker compose up
```

---

## Storage

| Variable | Value | Notes |
|---|---|---|
| `STORAGE_BACKEND` | `local` | Files written inside the container |
| `STORAGE_PATH` | `/app/openapi_storage` | Map this to a named or bind-mounted volume |

> **Important:** without a volume, files are lost when the container is recreated.
> Always map `STORAGE_PATH` to a Docker volume or a host bind mount if you need
> downloaded documents to persist.

### Bind mount (host path)

```yaml
    volumes:
      - type: bind
        source: ./openapi_storage
        target: /app/openapi_storage
```

### S3-compatible local storage (MinIO)

For a fully cloud-like setup without an actual cloud account, add MinIO to the
compose file and use `STORAGE_BACKEND=s3`:

```yaml
services:
  mcp:
    environment:
      STORAGE_BACKEND: "s3"
      STORAGE_BUCKET: "openapi-mcp"
      STORAGE_REGION: "us-east-1"
      AWS_ACCESS_KEY_ID: "minioadmin"
      AWS_SECRET_ACCESS_KEY: "minioadmin"
      AWS_ENDPOINT_URL: "http://minio:9000"

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data

volumes:
  minio_data:
```

---

## Cache

For a single-container local setup the in-process dict is sufficient (no cache
env vars needed). To share callback state across multiple replicas, add Redis:

```yaml
services:
  mcp:
    environment:
      CACHE_BACKEND: "redis"
      CACHE_URL: "redis://redis:6379"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Callbacks (async APIs)

The container must be reachable from the internet for async API callbacks.
Set `BASE_URL` to the public address of the host:

```yaml
    environment:
      BASE_URL: "https://my-server.example.com"
```

For local testing, use a tunnel (e.g. `ngrok http 8080`) and update `BASE_URL`
accordingly.

---

## Debug image

The `docker/dev/Dockerfile` adds `debugpy` on port 5678 and bind-mounts `./src`
for live code reload. The main `compose.yml` is already configured for this mode.
See the project `README.md` for the full VS Code one-click debug workflow.

---

## Full `compose.yml` example with Redis

```yaml
services:
  mcp:
    build:
      context: .
      dockerfile: docker/latest/Dockerfile
    ports:
      - "8080:8080"
    environment:
      PORT: "8080"
      BASE_URL: "https://my-server.example.com"
      SERVICES_CREDENTIALS: "{}"
      STORAGE_BACKEND: "local"
      STORAGE_PATH: "/app/openapi_storage"
      CACHE_BACKEND: "redis"
      CACHE_URL: "redis://redis:6379"
    volumes:
      - openapi_storage:/app/openapi_storage
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  openapi_storage:
```
