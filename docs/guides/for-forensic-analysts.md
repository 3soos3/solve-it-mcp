# For Forensic Analysts

This guide is for digital forensics professionals using the SOLVE-IT MCP Server in casework and investigations.

## Overview

SOLVE-IT MCP Server gives you instant programmatic access to a structured knowledge base of forensic techniques, their known weaknesses, and recommended mitigations. It is designed to support:

- **Technique selection**: Find the right method for a given evidence type or scenario
- **Methodology validation**: Identify and document the limitations of your chosen techniques
- **Report documentation**: Reference techniques, weaknesses, and mitigations by stable ID (DFT-XXXX, DFW-XXXX, DFM-XXXX)
- **Defensibility**: Demonstrate systematic, documented decision-making

## Quick Start

```bash
docker pull 3soos3/solve-it-mcp:latest
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  3soos3/solve-it-mcp:latest
```

Verify: `curl http://localhost:8000/healthz`

## Investigation Workflows

### Workflow 1: Finding the Right Technique

**Scenario**: You've seized a network router and need to determine the best approach for evidence extraction.

**Step 1 — Search for relevant techniques:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "network device",
        "item_types": ["techniques"]
      }
    }
  }'
```

**Step 2 — Review a technique in detail:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_technique_details",
      "arguments": {"technique_id": "DFT-1042"}
    }
  }'
```

**Step 3 — Identify potential weaknesses:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_weaknesses_for_technique",
      "arguments": {"technique_id": "DFT-1042"}
    }
  }'
```

**Step 4 — Find mitigations for a specific weakness:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 4,
    "method": "tools/call",
    "params": {
      "name": "get_mitigations_for_weakness",
      "arguments": {"weakness_id": "DFW-1015"}
    }
  }'
```

### Workflow 2: Investigation Planning by Objective

**Scenario**: Planning a mobile device investigation and ensuring comprehensive coverage.

**Step 1 — List available investigation objectives:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "list_objectives", "arguments": {}}
  }'
```

**Step 2 — Get all techniques for a specific objective:**

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_techniques_for_objective",
      "arguments": {"objective_name": "Mobile Device Forensics"}
    }
  }'
```

### Workflow 3: Methodology Validation

**Scenario**: Preparing expert testimony and needing to document strengths and limitations.

1. List all techniques used in the investigation
2. Call `get_weaknesses_for_technique` for each
3. Call `get_mitigations_for_weakness` for each weakness
4. Document the mitigations you implemented and why

**Example methodology section for a report:**

```markdown
## Investigation Methodology

### Network Traffic Analysis (DFT-1023)

**Purpose**: Identify suspicious network communications.

**Weaknesses considered**:
- DFW-1008: Encrypted traffic may not be fully analyzable
- DFW-1012: Incomplete packet capture due to tap limitations

**Mitigations applied**:
- DFM-1004: Captured full packet headers and metadata
- DFM-1009: Cross-referenced with firewall logs for context
- DFM-1015: Documented capture timestamps and chain of custody

**Justification**: Despite acknowledged limitations, this technique provided
crucial evidence of C2 communication patterns corroborating endpoint findings.
```

## Claude Desktop Integration

For interactive, natural-language analysis during investigations:

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "solveit": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "MCP_TRANSPORT=stdio",
        "3soos3/solve-it-mcp:latest"
      ]
    }
  }
}
```

Restart Claude Desktop. You can then ask questions naturally:

- "What techniques are available for memory forensics?"
- "What are the weaknesses of timeline analysis?"
- "Show me mitigations for DFW-1008"
- "Help me write the methodology section of my report covering DFT-1023"

## Offline and Field Use

The `:latest` and `:release` Docker images include the complete SOLVE-IT database. No internet connection is required after the initial pull, making the server suitable for:

- Isolated forensic workstations
- Air-gapped environments
- Field laptop deployments

For field use with reduced resource consumption:

```bash
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e LOG_LEVEL=WARNING \
  -e OTEL_ENABLED=false \
  3soos3/solve-it-mcp:latest
```

!!! warning "Do not use the `:live` image for forensic casework"
    The `:live` image fetches data at startup from a remote URL. Two containers started at different times may query different knowledge bases. For forensic reproducibility, always use `:release` images where the data is pinned at build time. See [Docker Images](../deployment/docker.md#image-types) for details.

## Forensic Reproducibility

For casework requiring a documented, citable record of which software version produced a result:

1. Use a `:release` image (e.g. `ghcr.io/3soos3/solve-it-mcp:v2025-10-abc1234`)
2. Enable `FORENSIC_METADATA=true` — every tool response will include a `_meta` block with the image tag and a UTC timestamp
3. Verify the image signature with Cosign (GHCR images only):

```bash
cosign verify ghcr.io/3soos3/solve-it-mcp:v2025-10-abc1234 \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com
```

## Automated Report Generation

Example script to generate a methodology section for a list of techniques:

```python
#!/usr/bin/env python3
import requests
import json

SERVER = "http://localhost:8000/mcp/v1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call_tool(name, arguments):
    r = requests.post(SERVER, headers=HEADERS, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    })
    r.raise_for_status()
    # SSE response: extract first data line
    for line in r.text.splitlines():
        if line.startswith("data:"):
            return json.loads(line[5:].strip())
    return {}

def technique_summary(tech_id):
    details = call_tool("get_technique_details", {"technique_id": tech_id})
    weaknesses = call_tool("get_weaknesses_for_technique", {"technique_id": tech_id})
    return {"id": tech_id, "details": details, "weaknesses": weaknesses}

techniques_used = ["DFT-1023", "DFT-1042", "DFT-1055"]
for tid in techniques_used:
    summary = technique_summary(tid)
    print(f"### {summary['id']}")
    print(json.dumps(summary, indent=2))
```

## Best Practices

**Documentation**

- Reference technique IDs in reports (e.g. "Network Traffic Analysis (DFT-1023)")
- Document weaknesses you identified and considered
- Justify mitigation choices explicitly
- Use consistent IDs across the investigation

**Defensibility**

- Show awareness of limitations before being challenged on them
- Document alternatives considered and why you chose otherwise
- Demonstrate a systematic, reproducible approach

**Court Reference**

SOLVE-IT is a published, peer-reviewed framework. To cite it:

> "SOLVE-IT Digital Forensics Framework (SOLVE-IT-DF/solve-it, https://github.com/SOLVE-IT-DF/solve-it)"

Always consult your legal team regarding expert testimony requirements in your jurisdiction.

## Next Steps

- [Tools Reference](../reference/tools-overview.md) — complete list of all 24 tools
- [Docker Deployment](../deployment/docker.md) — image types, tags, and security features
- [Security Model](../architecture/security-model.md) — chain-of-custody and verification
- [Troubleshooting](troubleshooting.md) — common issues
