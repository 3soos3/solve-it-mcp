# SOLVE-IT MCP Server

[![CI - Code Quality](https://github.com/3soos3/solve-it-mcp/workflows/CI%20-%20Code%20Quality%20%26%20Tests/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/ci.yml)
[![Security Scanning](https://github.com/3soos3/solve-it-mcp/workflows/Security%20-%20Vulnerability%20Scanning/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/security.yml)
[![License Compliance](https://github.com/3soos3/solve-it-mcp/workflows/License%20Compliance/badge.svg)](https://github.com/3soos3/solve-it-mcp/actions/workflows/license-compliance.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/3soos3/solve-it-mcp/badge)](https://securityscorecards.dev/viewer/?uri=github.com/3soos3/solve-it-mcp)
[![Docker Pulls](https://img.shields.io/docker/pulls/3soos3/solve-it-mcp)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![Docker Image Size](https://img.shields.io/docker/image-size/3soos3/solve-it-mcp/latest)](https://hub.docker.com/r/3soos3/solve-it-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Production-ready MCP server providing LLM access to the SOLVE-IT Digital Forensics Knowledge Base.**

SOLVE-IT is a systematic digital forensics knowledge base inspired by MITRE ATT&CK, containing comprehensive mappings of investigation techniques, weaknesses, and mitigations. This MCP server exposes the entire SOLVE-IT knowledge base through 20+ tools that enable LLMs to assist with digital forensics investigations.

## 🚀 Features

- **🔒 Production-Ready Security**: Alpine Linux base with zero CVEs, comprehensive security scanning
- **🌐 Multi-Platform Support**: Native images for AMD64, ARM64, and ARMv7 (Raspberry Pi)
- **📊 OpenTelemetry Observability**: Built-in metrics, tracing, and logging
- **⚡ High Performance**: Optimized shared knowledge base, sub-second response times
- **🔄 Dual Transport Modes**: HTTP/SSE for Kubernetes, stdio for desktop clients
- **📦 Minimal Footprint**: 181MB Alpine-based image (45% smaller than alternatives)
- **☸️ Kubernetes Native**: Production-grade Helm charts with health checks and auto-scaling

## What is SOLVE-IT?

SOLVE-IT provides a structured approach to digital forensics investigations through:

- **Techniques** (T1001, T1002...): Digital forensic investigation methods
- **Weaknesses** (W1001, W1002...): Potential problems/limitations of techniques  
- **Mitigations** (M1001, M1002...): Ways to address weaknesses
- **Objectives**: Categories that organize techniques by investigation goals

See the main repository: [SOLVE-IT-DF/solve-it](https://github.com/SOLVE-IT-DF/solve-it)

## 🔒 Security & Compliance

This project includes automated security scanning and best practices for forensic software:

### Automated Security
- ✅ **Vulnerability Scanning**: Trivy, Bandit, Safety, pip-audit
- ✅ **Code Review**: All PRs require review before merge
- ✅ **SBOM**: Software Bill of Materials (available on GHCR and as artifacts)
- ✅ **Image Signing**: Cryptographic signatures on GHCR images (Cosign)
- ✅ **License Compliance**: Automated dependency license checking
- ✅ **OpenSSF Scorecard**: Public security rating

### Forensic Verification (GHCR Images)

For maximum integrity and chain-of-custody, use GHCR images with Cosign:

```bash
# Verify image signature (proves authenticity)
cosign verify ghcr.io/3soos3/solve-it-mcp:latest \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# Download and inspect SBOM (see all dependencies)
cosign download sbom ghcr.io/3soos3/solve-it-mcp:latest | jq

# View build provenance (source commit, workflow, timestamp)
cosign download attestation ghcr.io/3soos3/solve-it-mcp:latest | jq
```

**Note**: Docker Hub images do NOT include Cosign signatures/SBOM to keep the tag list clean.

### For Production Use
**Important**: This is a best-effort maintained project. For critical forensic use:
- Perform your own security audit
- Review all dependencies and licenses
- Verify SBOM and image signatures
- Consider forking and maintaining your own version

See [SECURITY.md](SECURITY.md) for vulnerability reporting and security policy.

## 🐳 Docker Quick Start

**Recommended**: Use Docker for the easiest deployment experience.

### Choose Your Registry

**Docker Hub** (docker.io) - For general use:
```bash
docker pull 3soos3/solve-it-mcp:latest
```

**GitHub Container Registry** (ghcr.io) - For forensic verification:
```bash
docker pull ghcr.io/3soos3/solve-it-mcp:latest
```

**Which to use?**
- **Docker Hub**: Clean tags, best for production use
- **GHCR**: Includes cryptographic signatures and SBOM attachments for forensic verification

### Pull and Run

```bash
# Pull the latest stable image (SOLVE-IT 0.2025-10)
docker pull 3soos3/solve-it-mcp:latest

# Run in HTTP mode (for web/API access)
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e HTTP_PORT=8000 \
  3soos3/solve-it-mcp:latest

# Test health endpoint
curl http://localhost:8000/healthz

# Test MCP endpoint
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"method":"tools/list"}'
```

### Available Images

| Tag | Description | SOLVE-IT Version | Size |
|-----|-------------|------------------|------|
| `latest` | Latest stable release | 0.2025-10 | 181 MB |
| `stable` | Manual stable marker | 0.2025-10 | 181 MB |
| `v0.2025-10-0.1.0` | Specific version | 0.2025-10 | 181 MB |

**Architectures**: `linux/amd64`, `linux/arm64`, `linux/arm/v7`

**Base Image**: Alpine Linux 3.23 (zero CRITICAL/HIGH vulnerabilities)

For detailed Docker documentation, see [docs/DOCKER.md](docs/DOCKER.md).

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `http` or `stdio` |
| `HTTP_HOST` | `0.0.0.0` | HTTP server bind address |
| `HTTP_PORT` | `8000` | HTTP server port |
| `SOLVE_IT_DATA_PATH` | `/app/solve-it-main/data` | Path to SOLVE-IT data |
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FORMAT` | `json` | Log format: `json` or `text` |

### Docker Compose Example

```yaml
version: '3.8'
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - HTTP_PORT=8000
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
```

## ☸️ Kubernetes Deployment

For production Kubernetes deployments, use the official Helm chart:

```bash
# Add Helm repository
helm repo add solveit https://3soos3.github.io/solveit-charts
helm repo update

# Install with default values
helm install solveit-mcp solveit/solveit-mcp

# Or customize deployment
helm install solveit-mcp solveit/solveit-mcp \
  --set replicaCount=3 \
  --set resources.requests.memory=256Mi \
  --set ingress.enabled=true
```

**Features:**
- Horizontal Pod Autoscaling (HPA)
- Resource limits and requests
- Health checks (liveness, readiness, startup)
- OpenTelemetry integration
- Service mesh ready

See [docs/KUBERNETES.md](docs/KUBERNETES.md) for complete Kubernetes documentation.

## Quick Start (Local Development)

### 1. Prerequisites

Ensure you have the SOLVE-IT knowledge base available:

https://github.com/SOLVE-IT-DF/solve-it.git


### 2. Install the MCP Server

```bash
git clone <this-repository>
cd solve_it_mcp
pip install -e .
```

### 3. Run the Server

```bash
python3 src/server.py
```

### 4. Configure MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "solveit": {
      "command": "python3",
      "args": ["/path/to/solve_it_mcp/src/server.py"],
      "cwd": "/path/to/solve_it_mcp"
    }
  }
}
```

## Available Tools

The server provides 20 tools organized into functional categories:

### Core Information Tools

#### `get_database_description`
Get comprehensive overview of the SOLVE-IT database and server capabilities.

**Parameters:** None

**Example:**
```
Tool: get_database_description
Result: Complete database statistics and server information
```

#### `search`
Search across techniques, weaknesses, and mitigations using keywords.

**Parameters:**
- `keywords` (string): Search terms. Use quotes for exact phrases
- `item_types` (array, optional): Filter by type: `["techniques", "weaknesses", "mitigations"]`

**Examples:**
```
Tool: search
Parameters: {"keywords": "network analysis", "item_types": ["techniques"]}

Tool: search  
Parameters: {"keywords": "\"log analysis\""}
```

### Detailed Lookup Tools

#### `get_technique_details`
Retrieve complete information for a specific technique.

**Parameters:**
- `technique_id` (string): Technique ID (e.g., "T1002")

#### `get_weakness_details`
Retrieve detailed information for a specific weakness.

**Parameters:**
- `weakness_id` (string): Weakness ID (e.g., "W1001")

#### `get_mitigation_details`
Retrieve detailed information for a specific mitigation.

**Parameters:**
- `mitigation_id` (string): Mitigation ID (e.g., "M1001")

### Relationship Analysis Tools

#### `get_weaknesses_for_technique`
Find all weaknesses associated with a technique.

**Parameters:**
- `technique_id` (string): Technique ID

#### `get_mitigations_for_weakness`
Find all mitigations that address a specific weakness.

**Parameters:**
- `weakness_id` (string): Weakness ID

#### `get_techniques_for_weakness`
Find all techniques that have a specific weakness.

**Parameters:**
- `weakness_id` (string): Weakness ID

#### `get_weaknesses_for_mitigation`
Find all weaknesses addressed by a specific mitigation.

**Parameters:**
- `mitigation_id` (string): Mitigation ID

#### `get_techniques_for_mitigation`
Find all techniques that benefit from a specific mitigation.

**Parameters:**
- `mitigation_id` (string): Mitigation ID

### Objective Management Tools

#### `list_objectives`
List all objectives from the current mapping.

**Parameters:** None

#### `get_techniques_for_objective`
Get all techniques associated with a specific objective.

**Parameters:**
- `objective_name` (string): Name of the objective

#### `list_available_mappings`
Show all available objective mapping files.

**Parameters:** None

#### `load_objective_mapping`
Switch to a different objective mapping (e.g., carrier.json, dfrws.json).

**Parameters:**
- `filename` (string): Mapping filename (e.g., "carrier.json")

### Bulk Retrieval Tools

#### Concise Format Tools
- `get_all_techniques_with_name_and_id` - All techniques with ID and name only
- `get_all_weaknesses_with_name_and_id` - All weaknesses with ID and name only  
- `get_all_mitigations_with_name_and_id` - All mitigations with ID and name only

#### Full Detail Tools (Use with caution - large data)
- `get_all_techniques_with_full_detail` - All techniques with complete details
- `get_all_weaknesses_with_full_detail` - All weaknesses with complete details
- `get_all_mitigations_with_full_detail` - All mitigations with complete details

## Usage Examples

### Example 1: Finding Network Forensics Techniques

```bash
# Using HTTP API
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "network traffic analysis",
        "item_types": ["techniques"]
      }
    }
  }'
```

**Result**: Returns all network analysis techniques like packet capture, flow analysis, etc.

### Example 2: Investigation Workflow

```bash
# Step 1: Search for relevant technique
search(keywords="memory forensics")

# Step 2: Get technique details
get_technique_details(technique_id="T1023")

# Step 3: Check weaknesses
get_weaknesses_for_technique(technique_id="T1023")

# Step 4: Find mitigations
get_mitigations_for_weakness(weakness_id="W1015")
```

### Example 3: Exploring by Objective

```bash
# List all investigation objectives
list_objectives()

# Get techniques for specific objective
get_techniques_for_objective(objective_name="Data Recovery")

# Get details for specific technique
get_technique_details(technique_id="T1042")
```

### Example 4: Using with Claude Desktop

When configured with Claude Desktop, you can ask natural language questions:

```
User: "What techniques should I use for mobile device forensics?"

Claude: Let me search the SOLVE-IT database...
[Uses search tool with keywords="mobile device forensics"]

Claude: I found 15 relevant techniques:
- T1056: Mobile Device Acquisition
- T1057: App Data Extraction
- T1058: SIM Card Analysis
...

User: "What are the weaknesses of T1056?"

Claude: [Uses get_weaknesses_for_technique(technique_id="T1056")]
...
```

### Example 5: Bulk Analysis

```bash
# Get overview of all techniques (concise)
get_all_techniques_with_name_and_id()

# Filter in your application
# Then get full details for specific items
get_technique_details(technique_id="T1001")
get_technique_details(technique_id="T1002")
```

## Data Configuration

The server automatically looks for the SOLVE-IT knowledge base in these locations:

1. `../solve-it-main/` (adjacent to server directory)
2. `./solve-it-main/` (in current directory)
3. Environment variable `SOLVE_IT_DATA_PATH`

Ensure your SOLVE-IT data directory contains:
- `data/solve-it.json` (default objective mapping)
- `data/techniques/` (technique JSON files)
- `data/weaknesses/` (weakness JSON files)
- `data/mitigations/` (mitigation JSON files)

## Performance Considerations

- **Search operations**: Typically complete in <5 seconds
- **Bulk operations**: May take <10 seconds for full detail retrievals
- **Individual lookups**: Near-instant response
- **Relationship queries**: Optimized for fast traversal

## Error Handling

The server provides comprehensive error handling:

- **Missing data**: Graceful fallback with helpful error messages
- **Invalid IDs**: Clear feedback on incorrect technique/weakness/mitigation IDs
- **Connection issues**: Automatic retry and timeout handling
- **Large datasets**: Memory-efficient processing with warnings

## Integration Examples

### Claude Desktop

```json
{
  "mcpServers": {
    "solveit": {
      "command": "python3",
      "args": ["/path/to/solve_it_mcp/src/server.py"],
      "cwd": "/path/to/solve_it_mcp"
    }
  }
}
```

## Security Features

- **Read-only access**: Server only reads from the knowledge base
- **Input validation**: All parameters validated with Pydantic schemas
- **Timeout protection**: Automatic timeouts for long-running operations
- **Memory limits**: Protection against excessive memory usage
- **Path validation**: Secure file path handling

## Development

### Running Tests

```bash
# Run integration tests with real SOLVE-IT data
python3 -m pytest solve_it_mcp/tests/integration/ -v

# Run unit tests
python3 -m pytest solve_it_mcp/tests/unit/ -v
```

## Troubleshooting

### Common Issues

**"Knowledge base not found"**
- Ensure SOLVE-IT data is in `../solve-it-main/` or set `SOLVE_IT_DATA_PATH`
- Verify the data directory contains `data/solve-it.json`

**"Technique/Weakness/Mitigation not found"**
- Check ID format (e.g., "T1001", "W1001", "M1001")
- Use `search` tool to find valid IDs

**"Mapping file not found"**
- Use `list_available_mappings` to see available files
- Ensure mapping files are in `data/` directory

## Attribution

This project is a **fork** of the original [solve_it_mcp](https://github.com/CKE-Proto/solve_it_mcp) created by **CKE-Proto** (L3K-A).

### Original Author
- **Repository**: https://github.com/CKE-Proto/solve_it_mcp
- **Author**: CKE-Proto (L3K-A)
- **Original License**: MIT

### This Fork
This fork has been significantly enhanced with production-ready features:
- Enterprise CI/CD pipelines with parallel execution
- Multi-architecture Docker support (amd64, arm64, arm/v7)
- Security scanning and license compliance automation
- Dual registry publishing (Docker Hub + GHCR)
- SBOM generation and cryptographic image signing
- Comprehensive documentation and forensic verification support

All enhancements maintain the original MIT license and proper attribution.

## License

MIT License - See LICENSE file for details.

**Original work** Copyright (c) 2025 L3K-A (CKE-Proto)  
**Modifications and enhancements** Copyright (c) 2026 3soos3

## Contributing

This server is part of the SOLVE-IT ecosystem. Contributions welcome through:

1. Issue reports for bugs or missing features
2. Pull requests for improvements
3. Documentation enhancements
4. Additional tool implementations

---

**Ready to investigate?** Start with `get_database_description` to explore the knowledge base, then use `search` to find relevant techniques for your investigation.
