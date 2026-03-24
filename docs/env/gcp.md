# Environment: Google Cloud Platform

Deploy on Cloud Run (serverless) with Google Cloud Storage for files and
Memcached (Memory Store) for async callback caching.

This guide covers running `openapi-mcp-sdk` on Google Cloud Platform.
The codebase supports GCP-specific variables for compatibility with existing deployments;
this guide documents both that approach and the recommended explicit configuration.

---

## Architecture

```
Internet → Cloud Run (openapi-mcp-sdk server)
               │
               ├── Google Cloud Storage (file downloads)
               └── Memorystore Memcached (async callback cache, VPC-internal)
```

---

## Environment variables

```bash
# Core
MCP_PORT=8080
MCP_ENV=production
MCP_BASE_URL=https://mcp.openapi.com
MCP_CALLBACK_URL=https://mcp.openapi.com/callbacks
MCP_OPENAPI_ENV=                        # dev, test, sandbox (alias of test), or empty for production

# Storage
MCP_STORAGE_BACKEND=gcs
MCP_STORAGE_BUCKET=my-cloud-run-service     # name of the GCS bucket

# Cache
MCP_CACHE_BACKEND=memcached
MCP_CACHE_HOST=10.x.x.x                 # Memorystore VPC-internal IP
MCP_CACHE_PORT=11211

```

---

## Legacy variables (backward compatibility)

If you are using a Cloud Run deployment without migrating to the
explicit variables above, the following variables are still read:

| Variable | Effect |
|---|---|
| `K_SERVICE` | Auto-set by Cloud Run. Derives `MCP_BASE_URL` (`K_SERVICE.replace("-",".")`) and `MCP_OPENAPI_ENV` (from service name prefix), and selects the Memcached VPC IP. |

> **Migration path:** set `MCP_BASE_URL`, `MCP_OPENAPI_ENV`, `MCP_CACHE_HOST` explicitly
> and stop relying on `K_SERVICE`. This makes the server portable to any platform.

---

## Cloud Run deployment

### Cloud Run service YAML

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mcp-openapi-com
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/vpc-access-connector: projects/MY_PROJECT/locations/REGION/connectors/MY_CONNECTOR
        run.googleapis.com/vpc-access-egress: all-traffic
    spec:
      containers:
        - image: gcr.io/MY_PROJECT/openapi-mcp-sdk:latest
          ports:
            - containerPort: 8080
          env:
            - name: MCP_PORT
              value: "8080"
            - name: MCP_BASE_URL
              value: "https://mcp.openapi.com"
            - name: MCP_STORAGE_BACKEND
              value: "gcs"
            - name: MCP_STORAGE_BUCKET
              value: "mcp-openapi-com"
            - name: MCP_CACHE_BACKEND
              value: "memcached"
            - name: MCP_CACHE_HOST
              value: "10.x.x.x"
```

### Build and deploy

```bash
# Build
gcloud builds submit --tag gcr.io/MY_PROJECT/openapi-mcp-sdk

# Deploy
gcloud run deploy mcp-openapi-com \
  --image gcr.io/MY_PROJECT/openapi-mcp-sdk \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```

---

## Storage: Google Cloud Storage

1. Create a bucket (name it after the service for legacy compatibility, or use any name + set `MCP_STORAGE_BUCKET`):

   ```bash
   gsutil mb -l europe-west1 gs://mcp-openapi-com
   ```

2. Grant the Cloud Run service account write access:

   ```bash
   gsutil iam ch serviceAccount:MY_SA@MY_PROJECT.iam.gserviceaccount.com:objectAdmin \
     gs://mcp-openapi-com
   ```

3. Set the env vars:

   ```bash
   MCP_STORAGE_BACKEND=gcs
   MCP_STORAGE_BUCKET=mcp-openapi-com
   ```

Downloaded files are stored at `gs://MCP_STORAGE_BUCKET/<request_id>/<filename>` and
served via the `/status/{id}/files/{name}` endpoint.

---

## Cache: Memorystore Memcached

Memcached is used to share async callback results across multiple Cloud Run
instances (which are stateless and ephemeral).

1. Create a Memorystore Memcached instance inside the same VPC.
2. Set:

   ```bash
   MCP_CACHE_BACKEND=memcached
   MCP_CACHE_HOST=10.x.x.x        # discovery IP from Memorystore console
   MCP_CACHE_PORT=11211
   ```

3. Connect Cloud Run to the VPC via a Serverless VPC Access connector so it can
   reach the private IP.

> **Tip:** Redis (Memorystore for Redis) is a simpler alternative with better
> support for persistence. Use `MCP_CACHE_BACKEND=redis` and `MCP_CACHE_URL=redis://IP:6379`.

---

## Notes

# TODO: Remove legacy dependency — pymemcache ties the app to a VPC-internal Memcached instance
# with hardcoded IPs (see memory_store.py). Replace with an in-process dict for dev and
# a Redis client (redis-py) for production via MCP_CACHE_URL env var.
pymemcache
# TODO: Remove legacy dependency — google-cloud-storage ties file storage to GCS. Replace with
# a storage-agnostic solution (local filesystem for dev, pluggable via MCP_STORAGE_BACKEND env var).
google-cloud-storage
