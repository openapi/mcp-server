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
PORT=8080
BASE_URL=https://mcp.openapi.com
CALLBACK_URL=https://mcp.openapi.com/callbacks
SANDBOX_PREFIX=                         # leave empty for production

# Storage
STORAGE_BACKEND=gcs
STORAGE_BUCKET=my-cloud-run-service     # name of the GCS bucket

# Cache
CACHE_BACKEND=memcached
MEMCACHED_HOST=10.x.x.x                 # Memorystore VPC-internal IP
MEMCACHED_PORT=11211

# Credentials
SERVICES_CREDENTIALS={}                 # inject via Secret Manager
```

---

## Legacy variables (backward compatibility)

If you are using a Cloud Run deployment without migrating to the
explicit variables above, the following variables are still read:

| Variable | Effect |
|---|---|
| `K_SERVICE` | Auto-set by Cloud Run. Derives `BASE_URL` (`K_SERVICE.replace("-",".")`), `SANDBOX_PREFIX` (from service name prefix), and selects the Memcached VPC IP. |
| `X-DEV-VM` | Internal flag, selects dev Memcached IP. |

> **Migration path:** set `BASE_URL`, `SANDBOX_PREFIX`, `MEMCACHED_HOST` explicitly
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
            - name: PORT
              value: "8080"
            - name: BASE_URL
              value: "https://mcp.openapi.com"
            - name: STORAGE_BACKEND
              value: "gcs"
            - name: STORAGE_BUCKET
              value: "mcp-openapi-com"
            - name: CACHE_BACKEND
              value: "memcached"
            - name: MEMCACHED_HOST
              value: "10.x.x.x"
            - name: SERVICES_CREDENTIALS
              valueFrom:
                secretKeyRef:
                  name: services-credentials
                  key: latest
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

1. Create a bucket (name it after the service for legacy compatibility, or use any name + set `STORAGE_BUCKET`):

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
   STORAGE_BACKEND=gcs
   STORAGE_BUCKET=mcp-openapi-com
   ```

Downloaded files are stored at `gs://STORAGE_BUCKET/<request_id>/<filename>` and
served via the `/status/{id}/files/{name}` endpoint.

---

## Cache: Memorystore Memcached

Memcached is used to share async callback results across multiple Cloud Run
instances (which are stateless and ephemeral).

1. Create a Memorystore Memcached instance inside the same VPC.
2. Set:

   ```bash
   CACHE_BACKEND=memcached
   MEMCACHED_HOST=10.x.x.x        # discovery IP from Memorystore console
   MEMCACHED_PORT=11211
   ```

3. Connect Cloud Run to the VPC via a Serverless VPC Access connector so it can
   reach the private IP.

> **Tip:** Redis (Memorystore for Redis) is a simpler alternative with better
> support for persistence. Use `CACHE_BACKEND=redis` and `CACHE_URL=redis://IP:6379`.

---

## Credentials via Secret Manager

Store `SERVICES_CREDENTIALS` in Secret Manager and inject it at deploy time:

```bash
echo '{"my_service": "MY_API_KEY"}' | \
  gcloud secrets create services-credentials --data-file=-

gcloud run services update mcp-openapi-com \
  --update-secrets=SERVICES_CREDENTIALS=services-credentials:latest
```
