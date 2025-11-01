# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Housing Agent MCP application.

## Architecture

The application consists of the following services:

- **Frontend**: React application with ai-sdk-ui
- **BFF (Backend for Frontend)**: Go service handling API requests
- **Identity Service**: Go service for OTP authentication
- **Orchestrator Service**: Go service for room management
- **Agent/MCP Service**: Python service for tool execution
- **Payment Service**: Java Spring Boot service for payments
- **PostgreSQL**: Database for persistent storage
- **Redis**: Cache and session storage

## Prerequisites

- Kubernetes cluster (local with minikube or cloud provider)
- kubectl configured to access your cluster
- Docker images built and pushed to a registry

## Deployment Steps

1. **Create secrets** (update with your actual values):
   ```bash
   kubectl apply -f secrets.yaml
   ```

2. **Deploy database and cache**:
   ```bash
   kubectl apply -f postgres/
   kubectl apply -f redis/
   ```

3. **Deploy services**:
   ```bash
   kubectl apply -f bff/
   kubectl apply -f identity/
   kubectl apply -f orchestrator/
   kubectl apply -f agent-mcp/
   kubectl apply -f payment-service/
   ```

4. **Deploy frontend**:
   ```bash
   kubectl apply -f frontend/
   ```

5. **Deploy ingress** (optional, for external access):
   ```bash
   kubectl apply -f ingress.yaml
   ```

## Building Docker Images

Before deploying, you need to build and push Docker images:

```bash
# Build images
docker build -t housing/bff-service:latest ./services/bff
docker build -t housing/identity-service:latest ./services/identity
docker build -t housing/orchestrator-service:latest ./services/orchestrator
docker build -t housing/agent-mcp-service:latest ./services/agent-mcp
docker build -t housing/payment-service:latest ./services/payment-service
docker build -t housing/frontend:latest ./frontend

# Push to registry (replace with your registry)
docker tag housing/bff-service:latest your-registry/housing/bff-service:latest
docker push your-registry/housing/bff-service:latest
# ... repeat for other services
```

## Environment Variables

Update the deployment files with your actual environment variables:

- Database connection strings
- Redis URLs
- JWT secrets
- Twilio credentials
- Stripe API keys

## Monitoring

The services include health checks and resource limits. You can monitor them using:

```bash
# Check pod status
kubectl get pods

# Check service status
kubectl get services

# View logs
kubectl logs -f deployment/bff-service
```

## Scaling

To scale services:

```bash
kubectl scale deployment bff-service --replicas=3
kubectl scale deployment identity-service --replicas=3
# ... etc
```

## Cleanup

To remove all resources:

```bash
kubectl delete -f .
```
