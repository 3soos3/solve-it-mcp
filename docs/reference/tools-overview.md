# Tools Reference

Complete reference for all 20+ MCP tools provided by SOLVE-IT MCP Server.

!!! info "Work in Progress"
    This comprehensive tools reference is currently being developed. For now, please refer to the [Getting Started Guide](../getting-started.md) for basic tool usage.

## Available Tool Categories

### Core Information Tools
- `get_database_description` - Get comprehensive overview of SOLVE-IT database
- `search` - Search across techniques, weaknesses, and mitigations

### Detailed Lookup Tools
- `get_technique_details` - Retrieve complete technique information
- `get_weakness_details` - Retrieve detailed weakness information
- `get_mitigation_details` - Retrieve detailed mitigation information

### Relationship Analysis Tools
- `get_weaknesses_for_technique` - Find weaknesses for a technique
- `get_mitigations_for_weakness` - Find mitigations for a weakness
- `get_techniques_for_weakness` - Find techniques with a weakness
- `get_weaknesses_for_mitigation` - Find weaknesses addressed by mitigation
- `get_techniques_for_mitigation` - Find techniques benefiting from mitigation

### Objective Management Tools
- `list_objectives` - List all investigation objectives
- `get_techniques_for_objective` - Get techniques for an objective
- `list_available_mappings` - Show available objective mappings
- `load_objective_mapping` - Switch objective mapping
- `get_current_mapping` - Get active mapping name

### Bulk Retrieval Tools
- `get_bulk_techniques_list` - Get all technique IDs and names
- `get_bulk_weaknesses_list` - Get all weakness IDs and names
- `get_bulk_mitigations_list` - Get all mitigation IDs and names
- `get_bulk_techniques_full` - Get complete technique details
- `get_bulk_weaknesses_full` - Get complete weakness details
- `get_bulk_mitigations_full` - Get complete mitigation details

## Quick Examples

See the [Getting Started Guide](../getting-started.md) for usage examples.

## Need More Information?

- [Techniques Reference](techniques.md)
- [Weaknesses Reference](weaknesses.md)
- [Mitigations Reference](mitigations.md)
- [For Forensic Analysts Guide](../guides/for-forensic-analysts.md)
