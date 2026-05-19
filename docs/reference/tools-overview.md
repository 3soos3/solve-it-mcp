# Tools Overview

Complete reference for all 24 MCP tools provided by SOLVE-IT MCP Server.

## ID Conventions

| Prefix | Entity | Example |
|---|---|---|
| `DFT-XXXX` | Technique | `DFT-1001` |
| `DFW-XXXX` | Weakness | `DFW-1001` |
| `DFM-XXXX` | Mitigation | `DFM-1001` |
| `DFCite-XXXX` | Citation | `DFCite-0001` |

## Tool Categories

### Core Information

#### `get_database_description`

Returns the database structure, entity types, available objective mappings, and item counts.

Call this first to understand the knowledge base before using other tools.

**Parameters**: none

---

#### `search`

Search across techniques, weaknesses, and mitigations by keyword.

**Parameters**:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | string | yes | Search terms |
| `item_types` | array of strings | no | Limit to `"techniques"`, `"weaknesses"`, `"mitigations"` |
| `search_logic` | `"AND"` \| `"OR"` | no | Default: `"AND"` |
| `substring_match` | boolean | no | Match partial words. Default: `false` |

**Example**:

```json
{
  "keywords": "memory acquisition",
  "item_types": ["techniques"],
  "search_logic": "AND"
}
```

---

### Detailed Lookup

#### `get_technique_details`

Retrieve complete information for a technique by ID.

**Parameters**: `technique_id` (string, e.g. `"DFT-1001"`)

---

#### `get_weakness_details`

Retrieve complete information for a weakness by ID.

**Parameters**: `weakness_id` (string, e.g. `"DFW-1001"`)

---

#### `get_mitigation_details`

Retrieve complete information for a mitigation by ID.

**Parameters**: `mitigation_id` (string, e.g. `"DFM-1001"`)

---

### Relationship Analysis

These tools traverse the connections between entities.

#### `get_weaknesses_for_technique`

Find all weaknesses associated with a technique.

**Parameters**: `technique_id`

---

#### `get_mitigations_for_weakness`

Find all mitigations that address a weakness.

**Parameters**: `weakness_id`

---

#### `get_techniques_for_weakness`

Find all techniques that have a given weakness.

**Parameters**: `weakness_id`

---

#### `get_weaknesses_for_mitigation`

Find all weaknesses addressed by a mitigation.

**Parameters**: `mitigation_id`

---

#### `get_techniques_for_mitigation`

Find all techniques that benefit from a mitigation.

**Parameters**: `mitigation_id`

---

#### `get_mitigations_for_technique`

Shortcut: list mitigation IDs reachable from a technique (via its weaknesses).

**Parameters**: `technique_id`

---

#### `get_objectives_for_technique`

List the investigation objectives that a technique belongs to.

**Parameters**: `technique_id`

---

### Objective Management

#### `list_objectives`

List all investigation objectives available in the current mapping.

**Parameters**: none

---

#### `get_techniques_for_objective`

Get all techniques grouped under an investigation objective.

**Parameters**: `objective_name` (string)

---

#### `list_available_mappings`

Show all available objective mapping files (e.g. `solve-it`, `carrier`, `dfrws`).

**Parameters**: none

---

#### `load_objective_mapping`

Switch to a different objective mapping.

**Parameters**: `mapping_name` (string)

---

### Citation Tools

#### `get_citation`

Retrieve the full bibliographic text for a citation reference.

**Parameters**: `citation_id` (string, e.g. `"DFCite-0001"`)

---

#### `resolve_inline_citations`

Replace `[DFCite-XXXX]` markers in a text string with their full citation text.

**Parameters**: `text` (string containing inline citation markers)

---

### Bulk Retrieval

Bulk tools retrieve complete datasets in one call. Use for export, analysis, or Jupyter notebooks.

#### `get_all_techniques_with_name_and_id`

Returns a list of all technique IDs and names (lightweight).

**Parameters**: none

---

#### `get_all_weaknesses_with_name_and_id`

Returns a list of all weakness IDs and names (lightweight).

**Parameters**: none

---

#### `get_all_mitigations_with_name_and_id`

Returns a list of all mitigation IDs and names (lightweight).

**Parameters**: none

---

#### `get_all_techniques_with_full_detail`

Returns complete details for all techniques. Response may be large.

**Parameters**: none

---

#### `get_all_weaknesses_with_full_detail`

Returns complete details for all weaknesses. Response may be large.

**Parameters**: none

---

#### `get_all_mitigations_with_full_detail`

Returns complete details for all mitigations. Response may be large.

**Parameters**: none

---

## Tool Count Summary

| Category | Tools |
|---|---|
| Core Information | 2 |
| Detailed Lookup | 3 |
| Relationship Analysis | 7 |
| Objective Management | 4 |
| Citation | 2 |
| Bulk Retrieval | 6 |
| **Total** | **24** |

## Usage Examples

### Search then drill down

```bash
# 1. Search
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search","arguments":{"keywords":"disk imaging","item_types":["techniques"]}}}'

# 2. Get details for a result
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_technique_details","arguments":{"technique_id":"DFT-1055"}}}'

# 3. Find weaknesses
curl -X POST http://localhost:8000/mcp/v1/messages \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_weaknesses_for_technique","arguments":{"technique_id":"DFT-1055"}}}'
```

## Related Documentation

- [For Forensic Analysts](../guides/for-forensic-analysts.md) — investigation workflows
- [For Researchers](../guides/for-researchers.md) — bulk export and data analysis
- [Getting Started](../getting-started.md) — quick examples
