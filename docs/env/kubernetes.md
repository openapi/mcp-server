# Environment: Kubernetes

Deploy on any Kubernetes cluster (GKE, EKS, AKS, or on-prem) with a
PersistentVolumeClaim for local-style file storage, or an S3-compatible backend
(AWS S3, MinIO, GCS with interoperability) for shared storage across replicas.

---

## Architecture

```
Internet → Ingress → Service → Deployment (openapi-mcp-sdk pods)
                                     │
                                     ├── PersistentVolumeClaim  (local backend, single replica)
                                     │   or S3-compatible       (s3 backend, multiple replicas)
                                     └── Redis (ClusterIP)      (async callback cache)
```

---

## Namespace and ConfigMap

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: openapi-mcp
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: openapi-mcp-config
  namespace: openapi-mcp
data:
  MCP_PORT: "8080"
  MCP_BASE_URL: "https://mcp.example.com"
  MCP_STORAGE_BACKEND: "local"          # or "s3"
  MCP_STORAGE_PATH: "/app/openapi_storage"
  MCP_CACHE_BACKEND: "redis"
  MCP_CACHE_URL: "redis://redis-service:6379"
  MCP_OPENAPI_ENV: ""                  # dev, test, sandbox (alias of test), or empty for production
```

---

## Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: openapi-mcp-secret
  namespace: openapi-mcp
type: Opaque
stringData:
  # S3 credentials (only if MCP_STORAGE_BACKEND=s3 without IAM role):
  # AWS_ACCESS_KEY_ID: "..."
  # AWS_SECRET_ACCESS_KEY: "..."
```

---

## PersistentVolumeClaim (local backend)

Use this when running a single replica and you want files to persist across
pod restarts. For multi-replica deployments, use an S3-compatible backend instead
(multiple pods cannot safely share the same PVC with `ReadWriteOnce`).

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: openapi-storage-pvc
  namespace: openapi-mcp
spec:
  accessModes:
    - ReadWriteOnce      # single replica; use ReadWriteMany for NFS/CephFS
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard   # adjust to your cluster's storage class
```

---

## Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openapi-mcp-sdk
  namespace: openapi-mcp
spec:
  replicas: 1    # increase to >1 only when using s3/shared storage + Redis cache
  selector:
    matchLabels:
      app: openapi-mcp-sdk
  template:
    metadata:
      labels:
        app: openapi-mcp-sdk
    spec:
      containers:
        - name: openapi-mcp-sdk
          image: ghcr.io/openapi/mcp-server:latest
          ports:
            - containerPort: 8080
          envFrom:
            - configMapRef:
                name: openapi-mcp-config
            - secretRef:
                name: openapi-mcp-secret
          volumeMounts:
            - name: storage
              mountPath: /app/openapi_storage
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /status/readiness-check
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            # HTTP 404 is acceptable (request ID does not exist, server is alive)
            # Use a custom /health endpoint when available.
      volumes:
        - name: storage
          persistentVolumeClaim:
            claimName: openapi-storage-pvc
```

---

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: openapi-mcp-sdk
  namespace: openapi-mcp
spec:
  selector:
    app: openapi-mcp-sdk
  ports:
    - port: 80
      targetPort: 8080
```

---

## Ingress (nginx example)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openapi-mcp-sdk
  namespace: openapi-mcp
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - mcp.example.com
      secretName: openapi-mcp-tls
  rules:
    - host: mcp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: openapi-mcp-sdk
                port:
                  number: 80
```

---

## Redis (cache)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: openapi-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: openapi-mcp
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
```

---

## Multi-replica with S3 storage

To scale beyond one replica, switch to an S3-compatible backend so all pods share
the same file store:

```yaml
# In ConfigMap:
MCP_STORAGE_BACKEND: "s3"
MCP_STORAGE_BUCKET: "openapi-mcp-files"
MCP_STORAGE_REGION: "eu-west-1"

# In Deployment: remove the PVC volumeMount and volume
# In Deployment: replicas: 3

# In Secret (if not using IAM/IRSA):
AWS_ACCESS_KEY_ID: "..."
AWS_SECRET_ACCESS_KEY: "..."
```

With S3 + Redis, all replicas share state and the deployment can scale horizontally.

---

## Apply everything

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```
