# Kubernetes Examples for SOLVE-IT MCP Server

This directory contains simple Kubernetes deployment examples for quick testing.

## Recommended: Use Helm Chart

For production deployments, we strongly recommend using the official Helm chart instead of these manual examples:

```bash
# Add the Helm repository
helm repo add solveit https://3soos3.github.io/solveit-charts
helm repo update

# Install the chart
helm install solveit-mcp solveit/solveit-mcp
```

**Benefits of using Helm:**
- ✅ Production-ready configuration out of the box
- ✅ High availability with autoscaling
- ✅ Full observability integration (OpenTelemetry)
- ✅ Ingress and TLS support
- ✅ Multiple environment presets (demo, staging, production)
- ✅ Easy upgrades and rollbacks
- ✅ ConfigMap and Secret management

**Chart repository**: https://github.com/3soos3/solveit-charts

---

## Manual Deployment (Simple Example)

If you need to deploy without Helm for testing purposes:

### 1. Deploy to Kubernetes

```bash
# Apply the deployment
kubectl apply -f deployment-simple.yaml

# Check the deployment
kubectl get deployment solveit-mcp
kubectl get pods -l app=solveit-mcp

# Check the service
kubectl get service solveit-mcp
```

### 2. Test the Service

```bash
# Port-forward to access locally
kubectl port-forward svc/solveit-mcp 8000:8000

# In another terminal, test the endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### 3. View Logs

```bash
# View logs from all pods
kubectl logs -l app=solveit-mcp --tail=100 -f

# View logs from a specific pod
kubectl logs <pod-name> -f
```

### 4. Scale the Deployment

```bash
# Scale to 5 replicas
kubectl scale deployment solveit-mcp --replicas=5

# Verify scaling
kubectl get deployment solveit-mcp
kubectl get pods -l app=solveit-mcp
```

### 5. Update the Image

```bash
# Update to a new version
kubectl set image deployment/solveit-mcp \
  solveit-mcp=3soos3/solve-it-mcp:v0.2025-10

# Check rollout status
kubectl rollout status deployment/solveit-mcp

# Rollback if needed
kubectl rollout undo deployment/solveit-mcp
```

### 6. Clean Up

```bash
# Delete the deployment and service
kubectl delete -f deployment-simple.yaml

# Or delete individually
kubectl delete deployment solveit-mcp
kubectl delete service solveit-mcp
```

---

## What's Included

### deployment-simple.yaml

This manifest includes:

- **Deployment**: 2 replicas with health checks and resource limits
- **Service**: ClusterIP service exposing port 8000
- **Security**: Non-root user, dropped capabilities
- **Health Checks**: Liveness and readiness probes
- **Kubernetes Metadata**: Downward API for pod/node information

### Configuration

The deployment is configured for basic production use:

- **Replicas**: 2 (for basic high availability)
- **Resources**: 
  - Requests: 250m CPU, 256Mi memory
  - Limits: 1000m CPU, 512Mi memory
- **Health Checks**: 
  - Liveness: `/health` every 30s
  - Readiness: `/ready` every 10s
- **Transport**: HTTP mode (required for Kubernetes)
- **Logging**: JSON format, INFO level
- **OpenTelemetry**: Disabled by default (enable in Helm chart)

---

## Customization

### Enable OpenTelemetry

Edit the deployment to enable observability:

```yaml
env:
- name: OTEL_ENABLED
  value: "true"
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://otel-collector.observability.svc.cluster.local:4317"
```

### Change Log Level

For debug logging:

```yaml
env:
- name: LOG_LEVEL
  value: "DEBUG"
- name: LOG_FORMAT
  value: "text"  # Human-readable for development
```

### Adjust Resources

For higher load:

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 1Gi
```

### Expose via LoadBalancer

Change the service type:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: solveit-mcp
spec:
  type: LoadBalancer  # Changed from ClusterIP
  ports:
  - port: 80
    targetPort: 8000
```

---

## Production Deployment

**⚠️ These examples are for testing only.**

For production, use the Helm chart which provides:

- **Autoscaling**: HorizontalPodAutoscaler based on CPU/memory
- **Ingress**: TLS termination and domain routing
- **ConfigMaps**: Centralized configuration management
- **Secrets**: Secure credential handling
- **Network Policies**: Pod-to-pod communication controls
- **Pod Disruption Budgets**: Maintain availability during updates
- **Service Monitor**: Prometheus integration (if using Prometheus Operator)

**Get started with Helm:**

```bash
# Demo environment (minimal resources)
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.demo.yaml

# Staging environment (testing/validation)
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.staging.yaml \
  --namespace staging --create-namespace

# Production environment (full HA)
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.prod.yaml \
  --namespace production --create-namespace
```

---

## Resources

- **Full Kubernetes Documentation**: [docs/KUBERNETES.md](../../docs/KUBERNETES.md)
- **Helm Chart Repository**: https://github.com/3soos3/solveit-charts
- **Docker Images**: https://hub.docker.com/r/3soos3/solve-it-mcp
- **Docker Documentation**: [docs/DOCKER.md](../../docs/DOCKER.md)
