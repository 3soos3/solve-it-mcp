# SOLVE-IT MCP Server for Forensic Analysts

This guide is specifically designed for digital forensics professionals who want to leverage SOLVE-IT MCP Server in their investigations.

## Overview

As a forensic analyst, you're often faced with:

- **Complex evidence collection**: Choosing the right techniques for specific scenarios
- **Methodology validation**: Ensuring your investigation methods are sound
- **Weakness awareness**: Understanding limitations of your chosen techniques
- **Documentation requirements**: Providing detailed justification for your methods

SOLVE-IT MCP Server helps by providing instant access to a comprehensive knowledge base of forensic techniques, their weaknesses, and mitigations.

## Quick Start for Analysts

### Installation (2 minutes)

The fastest way to get started:

```bash
# Pull and run the Docker image
docker pull 3soos3/solve-it-mcp:latest
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e HTTP_PORT=8000 \
  3soos3/solve-it-mcp:latest
```

### Verify Installation

```bash
curl http://localhost:8000/healthz
```

You're ready when you see: `{"status":"healthy"}`

## Common Investigation Workflows

### Workflow 1: Finding the Right Technique

**Scenario**: You've seized a network router and need to determine the best approach for evidence extraction.

#### Step 1: Search for Relevant Techniques

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "network device extraction",
        "item_types": ["techniques"]
      }
    }
  }'
```

#### Step 2: Review Technique Details

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_technique_details",
      "arguments": {
        "technique_id": "T1042"
      }
    }
  }'
```

#### Step 3: Identify Potential Weaknesses

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_weaknesses_for_technique",
      "arguments": {
        "technique_id": "T1042"
      }
    }
  }'
```

#### Step 4: Find Mitigations

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_mitigations_for_weakness",
      "arguments": {
        "weakness_id": "W1015"
      }
    }
  }'
```

### Workflow 2: Validating Your Methodology

**Scenario**: You're preparing expert testimony and need to document the strengths and limitations of your chosen methods.

#### Document Your Approach

1. **List all techniques used** in your investigation
2. **Identify known weaknesses** for each technique
3. **Document mitigations** you've applied
4. **Cross-reference** with investigation objectives

#### Example Investigation Report Section

```markdown
## Investigation Methodology

### Technique: Network Traffic Analysis (T1023)

**Purpose**: Identify suspicious network communications

**Weaknesses Considered**:
- W1008: Encrypted traffic may not be fully analyzable
- W1012: Incomplete packet capture due to network tap limitations

**Mitigations Applied**:
- M1004: Captured full packet headers and metadata
- M1009: Cross-referenced with firewall logs for context
- M1015: Documented capture timestamps and chain of custody

**Justification**: Despite acknowledged limitations, this technique
provided crucial evidence of C2 communication patterns that
corroborated findings from endpoint analysis.
```

### Workflow 3: Investigation Planning

**Scenario**: You're planning a mobile device investigation and want to ensure comprehensive coverage.

#### Step 1: List All Relevant Objectives

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "list_objectives",
      "arguments": {}
    }
  }'
```

#### Step 2: Get Techniques for Your Objective

```bash
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_techniques_for_objective",
      "arguments": {
        "objective_name": "Mobile Device Forensics"
      }
    }
  }'
```

#### Step 3: Create Investigation Checklist

Use the returned techniques to build a comprehensive investigation plan.

## Integration with MCP Clients

### Claude Desktop Integration

For interactive analysis during investigations:

1. **Install Docker** (if not already installed)

2. **Configure Claude Desktop** (`claude_desktop_config.json`):

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

3. **Restart Claude Desktop**

4. **Ask questions naturally**:
   - "What techniques are available for memory forensics?"
   - "What are the weaknesses of timeline analysis?"
   - "Show me mitigations for hash collision issues"

### Benefits for Analysts

- **Natural language queries**: No need to remember exact technique IDs
- **Context-aware**: Claude can help interpret results in context of your investigation
- **Report drafting**: Use Claude to help write methodology sections
- **Training**: Ask "what if" questions to explore scenarios

## Practical Use Cases

### Use Case 1: Chain of Custody Documentation

**Challenge**: Documenting forensic soundness of your methods

**Solution**: Use SOLVE-IT to:

1. Identify all techniques applied
2. Document known weaknesses
3. Show mitigations implemented
4. Demonstrate forensic rigor

**Example Output for Court**:

> "The investigation employed SOLVE-IT Technique T1055 (Disk Imaging) 
> with documented awareness of Weakness W1032 (potential for hardware 
> read errors). Mitigation M1041 (verification hashing at multiple stages) 
> was implemented to ensure data integrity throughout the imaging process."

### Use Case 2: Peer Review Preparation

**Challenge**: Preparing evidence for peer review or opposing expert examination

**Solution**:

1. Document every technique used
2. Pre-identify weaknesses that might be challenged
3. Prepare justifications for mitigation choices
4. Demonstrate awareness of methodology limitations

### Use Case 3: Training and Skill Development

**Challenge**: Staying current with forensic methodologies

**Solution**:

- Explore new techniques in your domain
- Understand relationships between techniques
- Learn about weaknesses you may not have considered
- Discover mitigation strategies used by peers

**Example Training Exercise**:

```bash
# Explore all timeline analysis techniques
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "keywords": "timeline",
        "item_types": ["techniques"]
      }
    }
  }'
```

### Use Case 4: Cross-Platform Investigations

**Challenge**: Investigating across multiple platforms (Windows, Linux, mobile, cloud)

**Solution**: Use objectives to organize multi-platform approach

```bash
# Get techniques for cloud forensics
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_techniques_for_objective",
      "arguments": {
        "objective_name": "Cloud Forensics"
      }
    }
  }'
```

## Field Work Considerations

### Mobile Access

For field investigations, use the server on a laptop:

```bash
# Run with minimal logging for performance
docker run -p 8000:8000 \
  -e MCP_TRANSPORT=http \
  -e LOG_LEVEL=WARNING \
  -e HTTP_PORT=8000 \
  3soos3/solve-it-mcp:latest
```

### Offline Access

The Docker image includes the complete SOLVE-IT database:

- No internet required after initial pull
- All data embedded in the image
- Works on isolated forensic workstations

### Performance Optimization

For faster queries on resource-constrained systems:

```yaml
# docker-compose.yml for field laptop
version: '3.8'
services:
  solve-it-mcp:
    image: 3soos3/solve-it-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - MCP_TRANSPORT=http
      - LOG_LEVEL=ERROR
      - OTEL_ENABLED=false  # Disable telemetry
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
```

## Best Practices

### Documentation

1. **Reference Technique IDs** in your reports (e.g., "T1023: Network Traffic Analysis")
2. **Document weaknesses** you identified and considered
3. **Justify mitigation choices** explicitly
4. **Maintain consistency** across investigations

### Quality Assurance

1. **Cross-check techniques** with case requirements
2. **Review weaknesses** before finalizing methodology
3. **Peer review** your technique selections
4. **Update documentation** as new techniques emerge

### Defensibility

1. **Show awareness** of limitations
2. **Document alternatives** considered
3. **Justify selections** based on case specifics
4. **Demonstrate rigor** through systematic approach

## Common Questions

### Q: Can I use SOLVE-IT references in court?

**A**: Yes, SOLVE-IT is a published, peer-reviewed framework. Cite it as:

> "SOLVE-IT Digital Forensics Framework (SOLVE-IT-DF/solve-it, 
> https://github.com/SOLVE-IT-DF/solve-it)"

Always consult with your legal team regarding expert testimony requirements in your jurisdiction.

### Q: How often is the knowledge base updated?

**A**: The SOLVE-IT framework is actively maintained. Check for:

- New Docker image releases (monthly rebuilds)
- SOLVE-IT repository updates
- Release notes for version-specific changes

### Q: Can I add custom techniques for my organization?

**A**: The current implementation uses the official SOLVE-IT data. For custom extensions:

1. Fork the SOLVE-IT repository
2. Add your custom techniques
3. Rebuild the Docker image with your data
4. See [Contributing Guide](../development/contributing.md)

### Q: Is this suitable for sensitive investigations?

**A**: Yes, with proper deployment:

- **Runs locally**: No internet required
- **No data exfiltration**: All processing is local
- **Audit trail**: Full logging available
- **Isolated deployment**: Can run on air-gapped systems

See [Security Model](../architecture/security-model.md) for details.

## Integration Examples

### Example: Automated Report Generation

```python
#!/usr/bin/env python3
import requests
import json

def get_technique_details(tech_id):
    """Get full details for a technique"""
    response = requests.post(
        "http://localhost:8000/mcp/v1/messages",
        json={
            "method": "tools/call",
            "params": {
                "name": "get_technique_details",
                "arguments": {"technique_id": tech_id}
            }
        }
    )
    return response.json()

def generate_methodology_section(techniques):
    """Generate methodology section for report"""
    report = "## Investigation Methodology\n\n"
    
    for tech_id in techniques:
        details = get_technique_details(tech_id)
        # Parse and format details
        report += f"### Technique: {tech_id}\n"
        # Add details, weaknesses, mitigations
        
    return report

# Usage
techniques_used = ["T1023", "T1042", "T1055"]
methodology = generate_methodology_section(techniques_used)
print(methodology)
```

### Example: Technique Validation Script

```bash
#!/bin/bash
# validate-investigation.sh
# Validates that all techniques used have documented mitigations

TECHNIQUES=("T1023" "T1042" "T1055")

for tech in "${TECHNIQUES[@]}"; do
    echo "Checking $tech..."
    
    # Get weaknesses
    weaknesses=$(curl -s -X POST http://localhost:8000/mcp/v1/messages \
        -H "Content-Type: application/json" \
        -d "{\"method\":\"tools/call\",\"params\":{\"name\":\"get_weaknesses_for_technique\",\"arguments\":{\"technique_id\":\"$tech\"}}}")
    
    # Check if mitigations exist for each weakness
    # ... validation logic ...
    
    echo "$tech: Validated ✓"
done
```

## Next Steps

- **Explore the full tool set**: [Tools Reference](../reference/tools-overview.md)
- **Learn about data structure**: [Techniques](../reference/techniques.md), [Weaknesses](../reference/weaknesses.md), [Mitigations](../reference/mitigations.md)
- **Deploy in production**: [Kubernetes Guide](../deployment/kubernetes.md)
- **Integrate with your workflow**: [Integration Guide](integration.md)

## Need Help?

- **Troubleshooting**: [Common Issues](troubleshooting.md)
- **Questions**: [GitHub Discussions](https://github.com/3soos3/solve-it-mcp/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/3soos3/solve-it-mcp/issues)
