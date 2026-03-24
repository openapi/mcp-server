# Environment: Amazon Web Services

Deploy on ECS Fargate (serverless containers) with S3 for file storage and
ElastiCache Redis for async callback caching.

---

## Architecture

```
Internet → ALB → ECS Fargate (openapi-mcp-sdk server)
                 │
                 ├── S3 Bucket (file downloads)
                 └── ElastiCache Redis (async callback cache, VPC-internal)
```

---

## Environment variables

```bash
# Core
MCP_PORT=8080
MCP_BASE_URL=https://mcp.example.com      # ALB or CloudFront URL
MCP_CALLBACK_URL=https://mcp.example.com/callbacks
MCP_OPENAPI_ENV=                      # dev, test, sandbox (alias of test), or empty for production

# Storage
MCP_STORAGE_BACKEND=s3
MCP_STORAGE_BUCKET=openapi-mcp-files
MCP_STORAGE_REGION=eu-west-1

# Cache
MCP_CACHE_BACKEND=redis
MCP_CACHE_URL=redis://my-redis.cache.amazonaws.com:6379

```

---

## ECS Task Definition (excerpt)

```json
{
  "family": "openapi-mcp-sdk",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn":      "arn:aws:iam::ACCOUNT:role/openapi-mcp-task-role",
  "containerDefinitions": [
    {
      "name": "openapi-mcp-sdk",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/openapi-mcp-sdk:latest",
      "portMappings": [{ "containerPort": 8080 }],
      "environment": [
        { "name": "MCP_PORT",         "value": "8080" },
        { "name": "MCP_BASE_URL",     "value": "https://mcp.example.com" },
        { "name": "MCP_STORAGE_BACKEND",  "value": "s3" },
        { "name": "MCP_STORAGE_BUCKET",   "value": "openapi-mcp-files" },
        { "name": "MCP_STORAGE_REGION",   "value": "eu-west-1" },
        { "name": "MCP_CACHE_BACKEND",    "value": "redis" },
        { "name": "MCP_CACHE_URL",        "value": "redis://my-redis.cache.amazonaws.com:6379" }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/openapi-mcp-sdk",
          "awslogs-region": "eu-west-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## Build and push to ECR

```bash
# Authenticate
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com

# Build
docker build -t openapi-mcp-sdk -f docker/latest/Dockerfile .

# Tag and push
docker tag openapi-mcp-sdk:latest \
  ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/openapi-mcp-sdk:latest
docker push \
  ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/openapi-mcp-sdk:latest
```

---

## Storage: S3

1. Create an S3 bucket:

   ```bash
   aws s3 mb s3://openapi-mcp-files --region eu-west-1
   ```

2. Attach an IAM policy to the ECS task role (`openapi-mcp-task-role`):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
         "Resource": "arn:aws:s3:::openapi-mcp-files/*"
       }
     ]
   }
   ```

3. Configure the server:

   ```bash
   MCP_STORAGE_BACKEND=s3
   MCP_STORAGE_BUCKET=openapi-mcp-files
   MCP_STORAGE_REGION=eu-west-1
   ```

   AWS credentials are picked up automatically from the ECS task IAM role — no
   `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` needed in the container.

Downloaded files are stored at `s3://MCP_STORAGE_BUCKET/<request_id>/<filename>` and
served via the `/status/{id}/files/{name}` endpoint.

---

## Cache: ElastiCache Redis

1. Create a Redis cluster in the same VPC as the ECS tasks.
2. Allow the ECS security group to reach port 6379 on the ElastiCache security group.
3. Set:

   ```bash
   MCP_CACHE_BACKEND=redis
   MCP_CACHE_URL=redis://my-cluster.abc123.ng.0001.euw1.cache.amazonaws.com:6379
   ```

---

## Credentials via Secrets Manager

```bash
aws secretsmanager create-secret \
  --name openapi-mcp-credentials \
  --secret-string '{"my_service": "MY_API_KEY"}'
```

Reference the ARN in the task definition `secrets` block (see above).

---

## ALB health check

The ALB health check endpoint should call `GET /status/health`. The server returns
HTTP 404 with a JSON body for unknown request IDs — configure the ALB to accept
HTTP 404 as healthy, or add a dedicated `/health` endpoint if needed.
