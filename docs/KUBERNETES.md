# Kubernetes Deployment Guide - SOLVE-IT MCP Server

This guide covers deploying the SOLVE-IT MCP Server to Kubernetes clusters.

## Table of Contents

- [Quick Start with Helm](#quick-start-with-helm)
- [Manual Deployment](#manual-deployment)
- [Configuration](#configuration)
- [Health Checks](#health-checks)
- [Scaling](#scaling)
- [Observability](#observability)
- [Troubleshooting](#troubleshooting)

---

## Quick Start with Helm

**Recommended**: Use the official Helm chart for production deployments.

### Install Helm Chart

```bash
# Add the chart repository
helm repo add solveit https://3soos3.github.io/solveit-charts
helm repo update

# Install with default values (development-friendly)
helm install solveit-mcp solveit/solveit-mcp

# Or install for specific environment
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.prod.yaml

# Install to specific namespace
helm install solveit-mcp solveit/solveit-mcp \
  --namespace mcp \
  --create-namespace
```

### Environment-Specific Installations

The Helm chart provides pre-configured values files for different environments:

#### Demo Environment (Minimal Resources)

Perfect for demonstrations, workshops, and resource-constrained environments.

```bash
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.demo.yaml
```

**Features:**
- Single replica (no HA)
- Minimal CPU/memory requests
- No autoscaling
- OpenTelemetry disabled
- Simple configuration

#### Staging Environment (Testing & Validation)

For CI/CD testing, QA validation, and pre-production verification.

```bash
helm install solveit-mcp-staging solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.staging.yaml \
  --namespace staging \
  --create-namespace
```

**Features:**
- 2 replicas (test HA)
- Moderate resources
- Autoscaling 2-5 replicas
- Full observability enabled
- Ingress enabled with staging hostname

#### Production Environment (Full HA)

High-availability production deployment.

```bash
helm install solveit-mcp solveit/solveit-mcp \
  -f https://raw.githubusercontent.com/3soos3/solveit-charts/main/charts/solveit-mcp/values.prod.yaml \
  --namespace production \
  --create-namespace
```

**Features:**
- 3 replicas (high availability)
- Full resource limits
- Autoscaling 3-10 replicas (CPU-based)
- Full observability (OpenTelemetry)
- Ingress with TLS
- Production-grade configuration

### Verify Installation

```bash
# Check deployment status
helm status solveit-mcp

# Watch pods come up
kubectl get pods -l app.kubernetes.io/name=solveit-mcp --watch

# Test the service
kubectl port-forward svc/solveit-mcp 8000:8000
curl http://localhost:8000/health
```

### Chart Repository

- **Repository**: https://github.com/3soos3/solveit-charts
- **Chart Documentation**: https://github.com/3soos3/solveit-charts/tree/main/charts/solveit-mcp
- **Values Reference**: https://github.com/3soos3/solveit-charts/blob/main/charts/solveit-mcp/README.md

---

## Manual Deployment

For cases where you need to deploy without Helm, see the example manifests in `examples/k8s/`.

### Simple Deployment

```bash
# Apply basic deployment
kubectl apply -f examples/k8s/deployment-simple.yaml

# Verify deployment
kubectl get deployment solveit-mcp
kubectl get pods -l app=solveit-mcp

# Expose via service
kubectl expose deployment solveit-mcp --port=8000 --target-port=8000

# Port-forward for testing
kubectl port-forward deployment/solveit-mcp 8000:8000
```

See `examples/k8s/README.md` for more detailed examples.

---

## Configuration

### Environment Variables

Configure the server using environment variables in your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: solveit-mcp
        image: 3soos3/solve-it-mcp:stable
        env:
        # Transport (always HTTP in Kubernetes)
        - name: MCP_TRANSPORT
          value: "http"
        
        # HTTP configuration
        - name: HTTP_HOST
          value: "0.0.0.0"
        - name: HTTP_PORT
          value: "8000"
        
        # Logging
        - name: LOG_LEVEL
          value: "INFO"
        - name: LOG_FORMAT
          value: "json"
        
        # OpenTelemetry
        - name: OTEL_ENABLED
          value: "true"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector.observability.svc.cluster.local:4317"
        - name: ENVIRONMENT
          value: "production"
```

### Kubernetes Downward API

Inject pod/node metadata for better observability:

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

### ConfigMaps

For complex configurations:

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

### Liveness Probe

Restarts the pod if the server becomes unresponsive:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  timeoutSeconds: 3
  failureThreshold: 3
```

### Readiness Probe

Removes pod from service if not ready to handle requests:

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

Both probes are configured automatically in the Helm chart.

---

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment solveit-mcp --replicas=5

# Verify scaling
kubectl get deployment solveit-mcp
```

### Horizontal Pod Autoscaler (HPA)

The Helm chart includes HPA configuration. Enable it:

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
  --min=3 \
  --max=10 \
  --cpu-percent=70
```

### Resource Limits

Always set resource requests and limits:

```yaml
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 512Mi
```

---

## Observability

### OpenTelemetry Integration

The server exports telemetry to an OpenTelemetry collector:

**Requirements:**
1. Deploy OpenTelemetry Collector in your cluster
2. Configure the endpoint via environment variable

**Example OTel Collector deployment:**

```bash
# Install OpenTelemetry Operator
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml

# Deploy collector (example)
kubectl apply -f - <<EOF
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
  namespace: observability
spec:
  mode: daemonset
  config: |
    receivers:
      otlp:
        protocols:
          grpc:
          http:
    exporters:
      logging:
      prometheus:
        endpoint: "0.0.0.0:8889"
    service:
      pipelines:
        traces:
          receivers: [otlp]
          exporters: [logging]
        metrics:
          receivers: [otlp]
          exporters: [logging, prometheus]
EOF
```

**Configure SOLVE-IT MCP to use the collector:**

```yaml
env:
- name: OTEL_EXPORTER_OTLP_ENDPOINT
  value: "http://otel-collector.observability.svc.cluster.local:4317"
```

### Logging

Logs are written to stdout in JSON format. Collect them with your preferred tool:

- **Fluentd/Fluent Bit**
- **Promtail + Loki**
- **CloudWatch/Stackdriver** (cloud-native)

Filter logs by label:

```bash
kubectl logs -l app.kubernetes.io/name=solveit-mcp --tail=100 -f
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=solveit-mcp

# View pod events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

Common issues:
- Image pull errors (check `imagePullPolicy` and credentials)
- Resource limits too low (pod OOMKilled)
- Invalid configuration (check environment variables)

### Health Checks Failing

```bash
# Test health endpoint from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://solveit-mcp:8000/health

# Check if MCP_TRANSPORT=http
kubectl exec <pod-name> -- env | grep MCP_TRANSPORT
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints solveit-mcp

# Verify service configuration
kubectl describe service solveit-mcp

# Test from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://solveit-mcp.default.svc.cluster.local:8000/health
```

### High Memory Usage

Adjust resource limits:

```yaml
resources:
  limits:
    memory: 1Gi  # Increase from 512Mi
  requests:
    memory: 512Mi
```

Or check for memory leaks in logs:

```bash
kubectl logs <pod-name> | grep -i "memory\|oom"
```

---

## Next Steps

- **Helm Chart Documentation**: https://github.com/3soos3/solveit-charts
- **Production Best Practices**: Review the `values.prod.yaml` file
- **Observability Setup**: Configure OpenTelemetry collector for your environment
- **Ingress/TLS**: Set up ingress controller and TLS certificates

---

## Resources

- **Helm Chart Repository**: https://github.com/3soos3/solveit-charts
- **Docker Images**: https://hub.docker.com/r/3soos3/solve-it-mcp
- **MCP Specification**: https://modelcontextprotocol.io
- **SOLVE-IT Dataset**: https://github.com/SOLVE-IT-DF/solve-it
