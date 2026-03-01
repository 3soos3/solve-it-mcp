# SOLVE-IT MCP Server for Researchers

This guide is designed for academic researchers studying digital forensics, conducting empirical studies, or citing SOLVE-IT in scholarly work.

## Overview

SOLVE-IT MCP Server provides researchers with:

- **Structured access** to the complete SOLVE-IT digital forensics knowledge base
- **Reproducible queries** for empirical studies
- **Versioned data** for longitudinal research
- **Programmatic API** for automated analysis
- **Citation-ready** metadata and DOI references

## Citing This Software

### Academic Citation

If you use SOLVE-IT MCP Server in your research, please cite it:

```bibtex
@software{solve_it_mcp,
  author = {3soos3},
  title = {SOLVE-IT MCP Server: Production-ready MCP Server for Digital Forensics Knowledge Base},
  year = {2026},
  doi = {10.5281/zenodo.XXXXXXX},
  url = {https://github.com/3soos3/solve-it-mcp},
  version = {0.2025.10.0.1.0}
}
```

### Citing the SOLVE-IT Framework

Additionally, cite the underlying SOLVE-IT framework:

```bibtex
@misc{solveit_framework,
  author = {SOLVE-IT-DF},
  title = {SOLVE-IT: Standardized Framework for Digital Forensics Investigation},
  year = {2025},
  url = {https://github.com/SOLVE-IT-DF/solve-it},
  note = {Version 0.2025-10}
}
```

### APA Style

> 3soos3. (2026). *SOLVE-IT MCP Server: Production-ready MCP Server for Digital Forensics Knowledge Base* (Version 0.2025.10.0.1.0) [Computer software]. https://doi.org/10.5281/zenodo.XXXXXXX

### IEEE Style

> [1] 3soos3, "SOLVE-IT MCP Server: Production-ready MCP Server for Digital Forensics Knowledge Base," Version 0.2025.10.0.1.0, 2026. [Online]. Available: https://doi.org/10.5281/zenodo.XXXXXXX

## Research Use Cases

### Use Case 1: Empirical Analysis of Forensic Techniques

**Research Question**: How complete is the coverage of forensic techniques across different investigation objectives?

**Methodology**:

```bash
# Get all techniques
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_bulk_techniques_list",
      "arguments": {}
    }
  }' > all_techniques.json

# Get all objectives
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_objectives",
      "arguments": {}
    }
  }' > all_objectives.json

# Analyze coverage per objective
for objective in $(cat all_objectives.json | jq -r '.objectives[]'); do
    curl -X POST http://localhost:8000/mcp/v1/messages \
      -H "Content-Type: application/json" \
      -d "{
        \"method\": \"tools/call\",
        \"params\": {
          \"name\": \"get_techniques_for_objective\",
          \"arguments\": {
            \"objective_name\": \"$objective\"
          }
        }
      }" > "objective_${objective}.json"
done
```

### Use Case 2: Weakness-Mitigation Relationship Analysis

**Research Question**: What is the distribution of mitigations across weakness types?

**Methodology**:

```python
import requests
import json
import pandas as pd

def analyze_weakness_mitigation_coverage():
    # Get all weaknesses
    response = requests.post(
        "http://localhost:8000/mcp/v1/messages",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_bulk_weaknesses_list",
                "arguments": {}
            }
        }
    )
    weaknesses = response.json()
    
    # For each weakness, count mitigations
    coverage_data = []
    for weakness in weaknesses['weaknesses']:
        w_id = weakness['id']
        
        # Get mitigations for this weakness
        response = requests.post(
            "http://localhost:8000/mcp/v1/messages",
            json={
                "method": "tools/call",
                "params": {
                    "name": "get_mitigations_for_weakness",
                    "arguments": {"weakness_id": w_id}
                }
            }
        )
        mitigations = response.json()
        
        coverage_data.append({
            'weakness_id': w_id,
            'weakness_name': weakness['name'],
            'mitigation_count': len(mitigations.get('mitigations', []))
        })
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(coverage_data)
    
    # Statistical analysis
    print("Mitigation Coverage Statistics:")
    print(df['mitigation_count'].describe())
    
    # Identify gaps (weaknesses with few mitigations)
    gaps = df[df['mitigation_count'] < 2]
    print(f"\nWeaknesses with <2 mitigations: {len(gaps)}")
    
    return df

# Run analysis
results = analyze_weakness_mitigation_coverage()
results.to_csv('weakness_mitigation_analysis.csv', index=False)
```

### Use Case 3: Longitudinal Study of Framework Evolution

**Research Question**: How has the SOLVE-IT framework evolved over time?

**Methodology**:

1. **Version tracking**: Use Docker image tags to access historical versions

```bash
# Pull specific versions
docker pull 3soos3/solve-it-mcp:v0.2025-09-0.1.0
docker pull 3soos3/solve-it-mcp:v0.2025-10-0.1.0

# Run comparative analysis
# ... analyze differences between versions
```

2. **Data extraction**: Export complete datasets for each version

```bash
# Extract all data from a specific version
docker run --rm 3soos3/solve-it-mcp:v0.2025-10-0.1.0 \
  python3 -c "from solve_it_library import solve_it_library; \
    import json; \
    sil = solve_it_library(); \
    print(json.dumps({
      'techniques': sil.get_all_techniques_with_full_detail(),
      'weaknesses': sil.get_all_weaknesses_with_full_detail(),
      'mitigations': sil.get_all_mitigations_with_full_detail()
    }))" > solve_it_v0.2025-10.json
```

## Reproducibility Guidelines

### Version Specification

Always specify exact versions in your research:

```yaml
# research-environment.yml
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:v0.2025-10-0.1.0  # Specific version
    # ... configuration
```

### Data Provenance

Document the data lineage in your papers:

> "Data was accessed via SOLVE-IT MCP Server version 0.2025.10.0.1.0, 
> which includes SOLVE-IT framework data version 0.2025-10. The server 
> was run using Docker image 3soos3/solve-it-mcp:v0.2025-10-0.1.0 
> (SHA256: [digest]) to ensure reproducibility."

### Verification

Verify data integrity using image signatures:

```bash
# Verify Docker image signature
cosign verify ghcr.io/3soos3/solve-it-mcp:v0.2025-10-0.1.0 \
  --certificate-identity-regexp=github \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# Download SBOM
cosign download sbom ghcr.io/3soos3/solve-it-mcp:v0.2025-10-0.1.0 \
  > solve-it-mcp-sbom.json
```

Include SBOM in research data repositories for complete provenance.

## Dataset Access

### Complete Data Export

For offline analysis:

```bash
# Export all techniques with full details
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_bulk_techniques_full",
      "arguments": {}
    }
  }' | jq '.content[0].text | fromjson' > techniques_full.json

# Export all weaknesses with full details
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_bulk_weaknesses_full",
      "arguments": {}
    }
  }' | jq '.content[0].text | fromjson' > weaknesses_full.json

# Export all mitigations with full details
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_bulk_mitigations_full",
      "arguments": {}
    }
  }' | jq '.content[0].text | fromjson' > mitigations_full.json
```

### Data Structure

The SOLVE-IT knowledge base is organized as:

```
SOLVE-IT Framework
├── Techniques (T1001, T1002, ...)
│   ├── ID
│   ├── Name
│   ├── Description
│   ├── Procedure
│   ├── Weaknesses (references)
│   └── Objectives (references)
├── Weaknesses (W1001, W1002, ...)
│   ├── ID
│   ├── Name
│   ├── Description
│   ├── Related Techniques
│   └── Mitigations (references)
└── Mitigations (M1001, M1002, ...)
    ├── ID
    ├── Name
    ├── Description
    └── Addressed Weaknesses
```

See [Tools Overview](../reference/tools-overview.md) for available data access methods.

## Ethical Considerations

### Responsible Use

When conducting research using SOLVE-IT:

1. **Acknowledge limitations**: The framework is evolving and may not be comprehensive
2. **Avoid overgeneralization**: Findings are specific to the framework version studied
3. **Consider bias**: The framework reflects current forensic practices which may have inherent biases
4. **Protect privacy**: If combining with real-world data, ensure proper anonymization

### Human Subjects Research

If your research involves forensic practitioners:

- Obtain IRB approval where applicable
- Ensure informed consent
- Protect participant confidentiality
- Follow institutional research ethics guidelines

## Publishing Your Research

### Data Availability Statements

Example statement for your papers:

> **Data Availability**: This research used SOLVE-IT MCP Server version 
> 0.2025.10.0.1.0 (DOI: 10.5281/zenodo.XXXXXXX) with SOLVE-IT framework 
> data version 0.2025-10. The complete dataset is publicly available and 
> reproducible using Docker image 3soos3/solve-it-mcp:v0.2025-10-0.1.0. 
> Analysis scripts and processed data are available in our research 
> repository at [URL].

### Code and Data Sharing

Best practices for sharing your research:

```
research-repository/
├── README.md                 # Study overview
├── data/
│   ├── raw/                 # Raw SOLVE-IT exports
│   ├── processed/           # Your processed datasets
│   └── metadata.json        # Data provenance
├── scripts/
│   ├── 01_data_collection.py
│   ├── 02_analysis.py
│   └── 03_visualization.py
├── results/
│   ├── figures/
│   └── tables/
├── docker-compose.yml       # Exact environment specification
└── environment.yml          # Python environment
```

## Sample Research Projects

### Project Template: Technique Coverage Analysis

**Objective**: Analyze completeness of forensic technique documentation

**Data Collection**:

```python
#!/usr/bin/env python3
"""
Collect SOLVE-IT technique data for coverage analysis.
Research Project: Forensic Technique Documentation Completeness
Author: [Your Name]
Date: [Date]
"""

import requests
import json
from datetime import datetime

SERVER_URL = "http://localhost:8000/mcp/v1/messages"

def collect_all_techniques():
    """Collect complete technique dataset"""
    response = requests.post(
        SERVER_URL,
        json={
            "method": "tools/call",
            "params": {
                "name": "get_bulk_techniques_full",
                "arguments": {}
            }
        }
    )
    
    data = response.json()
    techniques = json.loads(data['content'][0]['text'])
    
    # Add metadata
    metadata = {
        'collection_date': datetime.utcnow().isoformat(),
        'server_version': '0.2025.10.0.1.0',
        'solveit_version': '0.2025-10',
        'technique_count': len(techniques)
    }
    
    return {
        'metadata': metadata,
        'techniques': techniques
    }

if __name__ == '__main__':
    dataset = collect_all_techniques()
    
    # Save with timestamp
    filename = f"techniques_dataset_{dataset['metadata']['collection_date']}.json"
    with open(filename, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"Dataset saved: {filename}")
    print(f"Techniques collected: {dataset['metadata']['technique_count']}")
```

## Integration with Research Tools

### Jupyter Notebook Integration

```python
# Install in notebook
!pip install requests pandas matplotlib

import requests
import pandas as pd
import matplotlib.pyplot as plt

# Query SOLVE-IT MCP Server
def query_solveit(tool_name, arguments):
    response = requests.post(
        "http://localhost:8000/mcp/v1/messages",
        json={
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
    )
    return response.json()

# Example: Analyze technique distribution
techniques = query_solveit("get_bulk_techniques_list", {})
df = pd.DataFrame(techniques['techniques'])

# Visualize
df['technique_category'].value_counts().plot(kind='bar')
plt.title('Distribution of Forensic Techniques by Category')
plt.xlabel('Category')
plt.ylabel('Count')
plt.show()
```

### R Integration

```r
library(httr)
library(jsonlite)

# Query SOLVE-IT MCP Server from R
query_solveit <- function(tool_name, arguments) {
  response <- POST(
    "http://localhost:8000/mcp/v1/messages",
    body = list(
      method = "tools/call",
      params = list(
        name = tool_name,
        arguments = arguments
      )
    ),
    encode = "json"
  )
  
  content(response, "parsed")
}

# Example usage
techniques <- query_solveit("get_bulk_techniques_list", list())
df <- as.data.frame(techniques$techniques)

# Statistical analysis
summary(df)
```

## Community Contributions

### Sharing Your Findings

Consider sharing your research findings with the SOLVE-IT community:

1. **GitHub Discussions**: Share insights and findings
2. **Pull Requests**: Suggest framework improvements based on your research
3. **Publications**: Link your papers in project discussions
4. **Datasets**: Share derived datasets (if permissible)

### Collaborative Research

Connect with other researchers:

- [SOLVE-IT Discussions](https://github.com/SOLVE-IT-DF/solve-it/discussions)
- [MCP Server Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- Digital forensics research conferences (DFRWS, etc.)

## License and Usage Rights

This software is licensed under the MIT License, allowing:

- ✅ Commercial and academic use
- ✅ Modification and distribution
- ✅ Private use
- ⚠️ **Requirement**: Include original license and copyright notice

See [LICENSE](https://github.com/3soos3/solve-it-mcp/blob/main/LICENSE) for full terms.

## Next Steps

- **Explore the data**: [Reference Documentation](../reference/tools-overview.md)
- **Set up environment**: [Getting Started](../getting-started.md)
- **Learn architecture**: [Architecture Overview](../architecture/overview.md)
- **Deploy for research**: [Kubernetes Deployment](../deployment/kubernetes.md)

## Getting Help

- **Research Questions**: [GitHub Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)
- **Collaboration**: Reach out via GitHub or academic conferences
