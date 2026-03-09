# Environment Configuration

This directory documents how to configure and deploy `openapi-mcp-sdk` in different
runtime environments.

Each environment file specifies the required environment variables, storage backend,
cache backend, and any platform-specific notes.

---

## Quick reference — all environment variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8080` | HTTP port the server listens on |
| `BASE_URL` | `https://mcp.openapi.com` | Public URL of this server (used in callback URLs) |
| `CALLBACK_URL` | `$BASE_URL/callbacks` | Full callback URL sent to async APIs |
| `SANDBOX_PREFIX` | _(empty)_ | Subdomain prefix for sandbox API endpoints (e.g. `dev.`) |
| `SERVICES_CREDENTIALS` | `{}` | JSON map of per-service API credentials |
| `STORAGE_BACKEND` | `local` | Storage backend: `local` \| `gcs` \| `s3` |
| `STORAGE_PATH` | `./openapi_storage` | Local filesystem path for `local` backend |
| `STORAGE_BUCKET` | _(required for cloud)_ | Bucket/container name for `gcs` or `s3` backend |
| `STORAGE_REGION` | _(required for s3)_ | AWS region for the S3 bucket |
| `CACHE_BACKEND` | `none` | Cache for async callbacks: `none` \| `memcached` \| `redis` |
| `MEMCACHED_HOST` | _(none)_ | Memcached host (used when `CACHE_BACKEND=memcached`) |
| `MEMCACHED_PORT` | `11211` | Memcached port |
| `CACHE_URL` | _(none)_ | Redis connection URL (used when `CACHE_BACKEND=redis`) |

### Legacy variables (GCP Cloud Run — deprecated)

These are still read by the current codebase for backward compatibility with the
existing GCP deployment. Prefer the explicit variables above for new deployments.

| Variable | Description |
|---|---|
| `K_SERVICE` | Cloud Run service name — auto-injects `BASE_URL`, `SANDBOX_PREFIX`, Memcached IPs |
| `X-DEV-VM` | Internal GCP dev-VM flag — affects Memcached IP selection |

---

## Why storage matters

Several openapi.com APIs return large binary responses (documents, reports, archives)
that cannot be embedded inline in the MCP JSON-RPC stream. The server downloads these
files, stores them, and returns a download link (`/status/{id}/files/{name}`) that
the MCP client can fetch separately.

The `visurecamerali` tool (Italian company official documents) is the primary example:
it downloads ZIP archives from the openapi.com backend and serves individual files
to the MCP client.

**Without a writable storage path the file-download APIs will fail.** Make sure the
configured backend is accessible, writable, and — if using `local` — that the path
survives process restarts if persistence is needed.

---

## Environment files

| File | Platform |
|---|---|
| [`local.md`](local.md) | Local machine or CI (default) |
| [`docker.md`](docker.md) | Docker / Docker Compose |
| [`gcp.md`](gcp.md) | Google Cloud Platform (Cloud Run + GCS + Memcached) |
| [`aws.md`](aws.md) | Amazon Web Services (ECS/Fargate + S3 + ElastiCache) |
| [`kubernetes.md`](kubernetes.md) | Kubernetes (any cloud or on-prem) |
