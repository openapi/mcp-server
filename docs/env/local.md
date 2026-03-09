# Environment: local (default)

Run the server directly on your machine or in a CI pipeline with no external
infrastructure. This is the default when no `STORAGE_BACKEND` is set.

All files downloaded from async APIs (e.g. visure camerali) are written to the
local filesystem. The server is the only process involved — no cloud accounts,
no storage buckets, no cache daemons required.

---

## Minimum configuration

```bash
export PORT=8080
export SERVICES_CREDENTIALS="{}"
```

Start the server:

```bash
uvx openapi-mcp-sdk server
# or
openapi-mcp-sdk server
```

The server is reachable at `http://localhost:8080`.

---

## Storage

| Variable | Value | Notes |
|---|---|---|
| `STORAGE_BACKEND` | `local` | Default — no need to set explicitly |
| `STORAGE_PATH` | `./openapi_storage` | Resolved relative to the working directory |

Downloaded files are saved to `$STORAGE_PATH/<request_id>/<filename>` and served
via `GET /status/{request_id}/files/{filename}`.

Override the path:

```bash
export STORAGE_PATH=/var/data/openapi_storage
```

> **Note for visure camerali and other document APIs:**
> The `STORAGE_PATH` directory is created automatically on first use. Make sure the
> user running the server has write permission to the parent directory. If you need
> the files to survive a server restart, point `STORAGE_PATH` at a persistent
> location (not `/tmp`).

---

## Cache

No cache daemon is needed. Async callback results are kept in an in-process
dictionary for the lifetime of the server process.

This is fine for single-instance local use. If you run multiple replicas or
need results to survive a restart, use a shared cache (see `docker.md`,
`kubernetes.md`, etc.).

---

## Callbacks (async APIs)

Async APIs (like visure camerali) send their result to a callback URL. In a local
setup the server must be reachable from the internet for callbacks to work.

Options:
- Use a tunnel: `ngrok http 8080` and set `BASE_URL` to the tunnel URL.
- Use a self-hosted reverse proxy with a public IP.

```bash
export BASE_URL=https://abc123.ngrok.io
```

If `BASE_URL` is not set the server defaults to `https://mcp.openapi.com`, which
will not work for local callbacks.

---

## Full example `.env` file

```bash
# local.env — source this before starting the server
PORT=8080
BASE_URL=https://abc123.ngrok.io   # replace with your tunnel URL

SERVICES_CREDENTIALS={}
STORAGE_BACKEND=local
STORAGE_PATH=./openapi_storage
```

```bash
source local.env && openapi-mcp-sdk server
```

---

## mcp-server.sh launcher (recommended)

```bash
cat > mcp-server.sh << 'EOF'
#!/bin/bash
export PORT="${PORT:-8080}"
export BASE_URL="${BASE_URL:-https://mcp.openapi.com}"
export SERVICES_CREDENTIALS="${SERVICES_CREDENTIALS:-{}}"
export STORAGE_BACKEND="${STORAGE_BACKEND:-local}"
export STORAGE_PATH="${STORAGE_PATH:-./openapi_storage}"

uvx openapi-mcp-sdk server
EOF
bash mcp-server.sh
```
