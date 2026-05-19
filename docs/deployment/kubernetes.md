# Kubernetes Deployment

This guide covers deploying SOLVE-IT MCP Server to Kubernetes.

## Quick Start with Helm

The recommended approach for production deployments uses the official Helm chart.

```bash
# Add the chart repository
helm repo add solveit https://3soos3.github.io/solveit-charts
helm repo update

# Install with defaults
helm install solveit-mcp solveit/solveit-mcp

# Install to a specific namespace
helm install solveit-mcp solveit/solveit-mcp \
  --namespace mcp \
  --create-namespace
```

### Environment-Specific Installations

**Demo (minimal resources):**

```bash
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.demo.yaml
```

**Staging (2 replicas, observability enabled):**

```bash
helm install solveit-mcp-staging solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.staging.yaml \
  --namespace staging --create-namespace
```

**Production (3 replicas, HA, TLS):**

```bash
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.prod.yaml \
  --namespace production --create-namespace
```

### Verify Installation

```bash
helm status solveit-mcp
kubectl get pods -l app.kubernetes.io/name=solveit-mcp --watch

# Test via port-forward
kubectl port-forward svc/solveit-mcp 8000:8000
curl http://localhost:8000/healthz
```

**Chart Repository**: https://github.com/3soos3/solveit-charts

---

## Manual Deployment

For deployments without Helm, use the example manifests from `examples/k8s/`.

```bash
kubectl apply -f examples/k8s/deployment-simple.yaml
kubectl expose deployment solveit-mcp --port=8000 --target-port=8000
kubectl port-forward deployment/solveit-mcp 8000:8000
```

---

## Configuration

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: solveit-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: solveit-mcp
  template:
    metadata:
      labels:
        app: solveit-mcp
    spec:
      containers:
      - name: solveit-mcp
        image: 3soos3/solve-it-mcp:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: MCP_TRANSPORT
          value: "http"
        - name: HTTP_HOST
          value: "0.0.0.0"
        - name: HTTP_PORT
          value: "8000"
        - name: LOG_LEVEL
          value: "INFO"
        - name: LOG_FORMAT
          value: "json"
        - name: OTEL_ENABLED
          value: "true"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector.observability.svc.cluster.local:4317"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1000
```

### Kubernetes Downward API

Inject pod metadata for better observability:

```yaml
env:
- name: K8S_POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: K8S_NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
- name: K8S_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
```

The Helm chart configures this automatically.

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: solveit-mcp-config
data:
  LOG_LEVEL: "INFO"
  OTEL_ENABLED: "true"
  ENVIRONMENT: "production"
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: solveit-mcp
        envFrom:
        - configMapRef:
            name: solveit-mcp-config
```

---

## Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readyz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

!!! note
    Use `/healthz` (liveness) and `/readyz` (readiness) — these are the primary endpoints. The legacy endpoints `/health` and `/ready` are deprecated.

---

## Scaling

### Manual Scaling

```bash
kubectl scale deployment solveit-mcp --replicas=5
```

### Horizontal Pod Autoscaler

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

Or apply manually:

```bash
kubectl autoscale deployment solveit-mcp \
  --min=3 --max=10 --cpu-percent=70
```

The server runs in stateless mode by default, enabling true horizontal scaling across pods.

---

## Observability

### OpenTelemetry

```yaml
env:
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://otel-collector.observability.svc.cluster.local:4317"
```

Install the OpenTelemetry Operator:

```bash
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml
```

### Logging

Logs are written to stdout in JSON format. Collect with Fluentd, Fluent Bit, Promtail, or your cloud provider's native log collector.

```bash
kubectl logs -l app.kubernetes.io/name=solveit-mcp --tail=100 -f
```

---

## Troubleshooting

### Pods Not Starting

```bash
kubectl get pods -l app.kubernetes.io/name=solveit-mcp
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

Common causes:

- Image pull errors — check `imagePullPolicy` and credentials
- OOMKilled — increase memory limit
- Invalid env var — check `MCP_TRANSPORT=http` is set

### Health Checks Failing

```bash
# Test from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://solveit-mcp:8000/healthz

# Check transport mode
kubectl exec <pod-name> -- env | grep MCP_TRANSPORT
```

### Service Not Accessible

```bash
kubectl get endpoints solveit-mcp
kubectl describe service solveit-mcp

# Test from inside the cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://solveit-mcp.default.svc.cluster.local:8000/healthz
```

### ImagePullBackOff for GHCR

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token>
```

---

## Next Steps

- [Helm Chart Documentation](https://github.com/3soos3/solveit-charts)
- [Docker Deployment](docker.md) — image types and tags
- [Environment Variables Reference](../reference/environment-variables.md)
