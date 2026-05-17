# Tools Reference

Complete reference for all 20+ MCP tools provided by SOLVE-IT MCP Server.

!!! info "Work in Progress"
    This comprehensive tools reference is currently being developed. For now, please refer to the [Getting Started Guide](../getting-started.md) for basic tool usage.

## Available Tool Categories

### Core Information Tools
- `get_database_description` - Get comprehensive overview of SOLVE-IT database
- `search` - Search across techniques, weaknesses, and mitigations (supports AND/OR logic and substring matching)

### Detailed Lookup Tools
- `get_technique_details` - Retrieve complete technique information (e.g. DFT-1001)
- `get_weakness_details` - Retrieve detailed weakness information (e.g. DFW-1001)
- `get_mitigation_details` - Retrieve detailed mitigation information (e.g. DFM-1001)

### Relationship Analysis Tools
- `get_weaknesses_for_technique` - Find weaknesses for a technique
- `get_mitigations_for_weakness` - Find mitigations for a weakness
- `get_techniques_for_weakness` - Find techniques with a weakness
- `get_weaknesses_for_mitigation` - Find weaknesses addressed by a mitigation
- `get_techniques_for_mitigation` - Find techniques benefiting from a mitigation
- `get_mitigations_for_technique` - Shortcut: list mitigation IDs directly from a technique ID
- `get_objectives_for_technique` - List objectives that a technique belongs to

### Objective Management Tools
- `list_objectives` - List all investigation objectives
- `get_techniques_for_objective` - Get techniques for an objective
- `list_available_mappings` - Show available objective mappings
- `load_objective_mapping` - Switch objective mapping

### Citation Tools
- `get_citation` - Retrieve formatted citation text for a DFCite-XXXX reference
- `resolve_inline_citations` - Replace [DFCite-XXXX] markers in text with full citation strings

### Bulk Retrieval Tools
- `get_all_techniques_with_name_and_id` - Get all technique IDs and names
- `get_all_weaknesses_with_name_and_id` - Get all weakness IDs and names
- `get_all_mitigations_with_name_and_id` - Get all mitigation IDs and names
- `get_all_techniques_with_full_detail` - Get complete details for all techniques
- `get_all_weaknesses_with_full_detail` - Get complete details for all weaknesses
- `get_all_mitigations_with_full_detail` - Get complete details for all mitigations

## Quick Examples

See the [Getting Started Guide](../getting-started.md) for usage examples.

## Need More Information?

- [For Forensic Analysts Guide](../guides/for-forensic-analysts.md)
- [For Researchers Guide](../guides/for-researchers.md)
- [Architecture Overview](../architecture/overview.md)
