# For Researchers

This guide is for academic researchers studying digital forensics, conducting empirical studies, or citing SOLVE-IT in scholarly work.

## Citing This Software

### BibTeX

```bibtex
@software{solve_it_mcp,
  author  = {3soos3},
  title   = {SOLVE-IT MCP Server: Production-ready MCP Server for Digital Forensics Knowledge Base},
  year    = {2026},
  doi     = {10.5281/zenodo.XXXXXXX},
  url     = {https://github.com/3soos3/solve-it-mcp},
  version = {0.2025.10.0.1.0}
}
```

### Citing the SOLVE-IT Framework

Also cite the underlying framework:

```bibtex
@misc{solveit_framework,
  author = {SOLVE-IT-DF},
  title  = {SOLVE-IT: Standardized Framework for Digital Forensics Investigation},
  year   = {2025},
  url    = {https://github.com/SOLVE-IT-DF/solve-it},
  note   = {Version 0.2025-10}
}
```

### APA

> 3soos3. (2026). *SOLVE-IT MCP Server* (Version 0.2025.10.0.1.0) [Computer software]. https://doi.org/10.5281/zenodo.XXXXXXX

### IEEE

> [1] 3soos3, "SOLVE-IT MCP Server," Version 0.2025.10.0.1.0, 2026. [Online]. Available: https://doi.org/10.5281/zenodo.XXXXXXX

## Reproducibility

### Pin the Exact Version

Always specify an exact image tag in your research environment, never use `:latest`:

```yaml
# research-environment.yml
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:v0.2025-10-abc1234
```

### Data Provenance Statement

Example statement for papers:

> Data was accessed via SOLVE-IT MCP Server version 0.2025.10.0.1.0, which includes SOLVE-IT framework data version 0.2025-10. The server was run using Docker image `3soos3/solve-it-mcp:v0.2025-10-0.1.0` (SHA256: [digest]) to ensure reproducibility.

### Cryptographic Verification

Verify image integrity using Cosign (GHCR images carry signatures and SBOM):

```bash
cosign verify ghcr.io/3soos3/solve-it-mcp:v0.2025-10-0.1.0 \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

cosign download sbom ghcr.io/3soos3/solve-it-mcp:v0.2025-10-0.1.0 \
  > solve-it-mcp-sbom.json
```

Include the SBOM in your research data repository for complete provenance.

!!! note "Use `:release` images for research"
    The `:release` image has both SOLVE-IT data and MCP code pinned at build time, and enables `FORENSIC_METADATA=true` by default. Each tool response includes a `_meta` block with the exact image tag and timestamp. This makes outputs citable and auditable. See [image types](../deployment/docker.md#image-types) for the full comparison.

## Research Use Cases

### Empirical Analysis of Technique Coverage

```bash
# Export all techniques
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 1,
    "method": "tools/call",
    "params": {"name": "get_all_techniques_with_full_detail", "arguments": {}}
  }' > all_techniques.json

# Export all weaknesses
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 2,
    "method": "tools/call",
    "params": {"name": "get_all_weaknesses_with_full_detail", "arguments": {}}
  }' > all_weaknesses.json

# Export all mitigations
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0", "id": 3,
    "method": "tools/call",
    "params": {"name": "get_all_mitigations_with_full_detail", "arguments": {}}
  }' > all_mitigations.json
```

### Weakness–Mitigation Coverage Analysis (Python)

```python
import requests
import json
import pandas as pd

SERVER = "http://localhost:8000/mcp/v1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call_tool(name, arguments=None):
    r = requests.post(SERVER, headers=HEADERS, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}}
    })
    for line in r.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            text = payload.get("result", {}).get("content", [{}])[0].get("text", "{}")
            return json.loads(text)
    return {}

weaknesses = call_tool("get_all_weaknesses_with_name_and_id")

coverage_data = []
for w in weaknesses.get("weaknesses", []):
    mitigations = call_tool("get_mitigations_for_weakness", {"weakness_id": w["id"]})
    coverage_data.append({
        "weakness_id": w["id"],
        "weakness_name": w["name"],
        "mitigation_count": len(mitigations.get("mitigations", []))
    })

df = pd.DataFrame(coverage_data)
print(df["mitigation_count"].describe())
gaps = df[df["mitigation_count"] < 2]
print(f"Weaknesses with <2 mitigations: {len(gaps)}")
df.to_csv("weakness_mitigation_coverage.csv", index=False)
```

### Jupyter Notebook Integration

```python
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt

SERVER = "http://localhost:8000/mcp/v1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
}

def call_tool(name, arguments=None):
    r = requests.post(SERVER, headers=HEADERS, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}}
    })
    for line in r.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            text = payload.get("result", {}).get("content", [{}])[0].get("text", "{}")
            return json.loads(text)
    return {}

data = call_tool("get_all_techniques_with_name_and_id")
techniques = data.get("techniques", [])
print(f"Total techniques: {len(techniques)}")
```

### R Integration

```r
library(httr)
library(jsonlite)

call_tool <- function(tool_name, arguments = list()) {
  response <- POST(
    "http://localhost:8000/mcp/v1/messages",
    add_headers(
      "Content-Type" = "application/json",
      "Accept" = "application/json, text/event-stream"
    ),
    body = list(
      jsonrpc = "2.0", id = 1,
      method = "tools/call",
      params = list(name = tool_name, arguments = arguments)
    ),
    encode = "json"
  )
  content(response, "parsed")
}

techniques <- call_tool("get_all_techniques_with_name_and_id")
```

## Data Structure

The SOLVE-IT knowledge base is organized as:

```
SOLVE-IT Framework
├── Techniques (DFT-XXXX)
│   ├── ID, Name, Description, Procedure
│   ├── Weaknesses (references to DFW-XXXX)
│   └── Objectives (references)
├── Weaknesses (DFW-XXXX)
│   ├── ID, Name, Description
│   ├── Related Techniques
│   └── Mitigations (references to DFM-XXXX)
├── Mitigations (DFM-XXXX)
│   ├── ID, Name, Description
│   └── Addressed Weaknesses
└── Citations (DFCite-XXXX)
    └── Full bibliographic text
```

## Publishing Your Research

### Data Availability Statement

> **Data Availability**: This research used SOLVE-IT MCP Server version 0.2025.10.0.1.0 (DOI: 10.5281/zenodo.XXXXXXX) with SOLVE-IT framework data version 0.2025-10. The complete dataset is publicly available and reproducible using Docker image `3soos3/solve-it-mcp:v0.2025-10-0.1.0`. Analysis scripts and processed data are available at [URL].

### Recommended Repository Structure

```
research-repository/
├── README.md
├── docker-compose.yml          # Exact image version pinned
├── data/
│   ├── raw/                    # Raw SOLVE-IT exports
│   ├── processed/              # Your processed datasets
│   └── metadata.json           # Data provenance
└── scripts/
    ├── 01_collect.py
    ├── 02_analyze.py
    └── 03_visualize.py
```

## Ethical Considerations

- **Acknowledge limitations**: The framework is evolving and may not be comprehensive
- **Avoid overgeneralization**: Findings are specific to the framework version studied
- **Protect privacy**: If combining with real-world case data, apply proper anonymization
- **Follow IRB/ethics guidelines** when your research involves human subjects

## Community

- [SOLVE-IT Discussions](https://github.com/SOLVE-IT-DF/solve-it/discussions)
- [MCP Server Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- Digital forensics conferences: DFRWS, IFIP WG 11.9

## License

MIT License — allows commercial and academic use, modification, and distribution. Attribution required.

## Next Steps

- [Tools Reference](../reference/tools-overview.md) — all 24 available tools
- [Getting Started](../getting-started.md) — quick setup
- [Docker Deployment](../deployment/docker.md) — image types and tags for pinning versions
