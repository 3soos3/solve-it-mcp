"""SOLVE-IT MCP Tools - Core tools for accessing the SOLVE-IT knowledge base."""

import json
from typing import Literal

from pydantic import Field

from .solveit_base import SolveItBaseTool, ToolParams


class GetDatabaseDescriptionParams(ToolParams):
    """Parameters for get_database_description tool."""

    pass


class GetDatabaseDescriptionTool(SolveItBaseTool[GetDatabaseDescriptionParams]):
    """Tool to get a comprehensive description of the SOLVE-IT database."""

    name = "get_database_description"
    description = (
        "Call this first to understand the SOLVE-IT knowledge base before using other tools. "
        "Returns the database structure, entity types (techniques DFT-XXXX, weaknesses DFW-XXXX, "
        "mitigations DFM-XXXX, citations DFCite-XXXX), available objective mappings, and item counts. "
        "Use this to orient yourself before searching or retrieving specific items."
    )
    Params = GetDatabaseDescriptionParams

    async def invoke(self, params: GetDatabaseDescriptionParams) -> str:
        """Get database description and server information."""
        try:
            stats = self.get_knowledge_base_stats()

            description = {
                "database_name": "SOLVE-IT Digital Forensics Knowledge Base",
                "description": "A systematic digital forensics knowledge base inspired by MITRE ATT&CK",
                "purpose": "Provides comprehensive mapping of digital forensic investigation techniques, weaknesses, and mitigations",
                "components": {
                    "techniques": "Digital forensic investigation methods (DFT-1001, DFT-1002, etc.)",
                    "weaknesses": "Potential problems/limitations of techniques (DFW-1001, DFW-1002, etc.)",
                    "mitigations": "Ways to address weaknesses (DFM-1001, DFM-1002, etc.)",
                    "objectives": "Investigation workflow phases that group techniques (e.g. 'Acquire data', 'Preserve digital evidence')",
                    "citations": "Academic and industry references cited by techniques and weaknesses (DFCite-XXXX)",
                },
                "statistics": stats,
                "mcp_server_role": "This MCP server provides LLMs with programmatic access to the SOLVE-IT knowledge base through type-safe, validated tools",
                "available_operations": [
                    "Search across techniques, weaknesses, and mitigations by keyword",
                    "Retrieve detailed information by ID",
                    "Explore relationships between components",
                    "Resolve citations (DFCite-XXXX) to full bibliographic text",
                    "Work with different objective mappings (solve-it, carrier, dfrws)",
                    "Bulk retrieval operations",
                ],
            }

            return self._wrap_response(json.dumps(description, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "database description retrieval")
            )


class SearchParams(ToolParams):
    """Parameters for search tool."""

    keywords: str = Field(
        description=(
            "Keywords to search for across name and description fields. "
            "Use quotes for exact phrases (e.g. '\"memory acquisition\"'). "
            "Multiple words are combined using search_logic (AND by default)."
        ),
        min_length=1,
    )
    item_types: list[str] | None = Field(
        default=None,
        description=(
            "Limit search to specific entity types: 'techniques', 'weaknesses', 'mitigations'. "
            "If omitted, searches all three types."
        ),
    )
    search_logic: Literal["AND", "OR"] = Field(
        default="AND",
        description=(
            "How to combine multiple keywords. "
            "'AND' (default) requires all terms to match — use for precise queries. "
            "'OR' requires any term to match — use for broader discovery."
        ),
    )
    substring_match: bool = Field(
        default=False,
        description=(
            "When True, matches any substring within a word (e.g. 'mem' matches 'memory'). "
            "When False (default), requires whole-word matches. "
            "Use True for partial-term or prefix searches."
        ),
    )


class SearchTool(SolveItBaseTool[SearchParams]):
    """Tool to search the knowledge base for techniques, weaknesses, or mitigations."""

    name = "search"
    description = (
        "Search SOLVE-IT by keyword when you don't know the exact ID. "
        "Searches name and description fields across techniques, weaknesses, and mitigations. "
        "Returns matching items sorted by relevance. "
        "Use this as the starting point for discovery — then call get_technique_details, "
        "get_weakness_details, or get_mitigation_details with the IDs from the results. "
        "Prefer 'AND' logic for precise queries, 'OR' for broader exploration."
    )
    Params = SearchParams

    async def invoke(self, params: SearchParams) -> str:
        """Search the knowledge base."""
        try:
            results = self.knowledge_base.search(
                keywords=params.keywords,
                item_types=params.item_types,
                search_logic=params.search_logic,
                substring_match=params.substring_match,
            )

            return self._wrap_response(json.dumps(results, indent=2))

        except Exception as e:
            return self._wrap_response(self.handle_knowledge_base_error(e, "search operation"))


class GetTechniqueDetailsParams(ToolParams):
    """Parameters for get_technique_details tool."""

    technique_id: str = Field(description="The technique ID (e.g., DFT-1002)", min_length=1)


class GetTechniqueDetailsTool(SolveItBaseTool[GetTechniqueDetailsParams]):
    """Tool to retrieve full details for a specific SOLVE-IT technique."""

    name = "get_technique_details"
    description = (
        "Retrieve full details for a technique by its DFT-XXXX ID. "
        "The response includes name, description, subtechniques, and a 'weaknesses' list of DFW-XXXX IDs. "
        "References appear as DFCite-XXXX IDs — call get_citation to resolve them to full bibliographic text. "
        "Use get_weaknesses_for_technique to get weakness details in one step instead of resolving each DFW-XXXX manually."
    )
    Params = GetTechniqueDetailsParams

    async def invoke(self, params: GetTechniqueDetailsParams) -> str:
        """Get technique details."""
        try:
            technique = self.knowledge_base.get_technique(params.technique_id)

            if technique is None:
                return self._wrap_response(f"Technique {params.technique_id} not found.")

            return self._wrap_response(json.dumps(technique, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"technique {params.technique_id} retrieval")
            )


class GetWeaknessDetailsParams(ToolParams):
    """Parameters for get_weakness_details tool."""

    weakness_id: str = Field(description="The weakness ID (e.g., DFW-1001)", min_length=1)


class GetWeaknessDetailsTool(SolveItBaseTool[GetWeaknessDetailsParams]):
    """Tool to retrieve details for a specific SOLVE-IT weakness."""

    name = "get_weakness_details"
    description = (
        "Retrieve details for a weakness by its DFW-XXXX ID. "
        "The 'name' field is the primary description of what can go wrong. "
        "The response includes ASTM error categories and a 'mitigations' list of DFM-XXXX IDs. "
        "Use get_mitigations_for_weakness to resolve those IDs to full mitigation details in one step."
    )
    Params = GetWeaknessDetailsParams

    async def invoke(self, params: GetWeaknessDetailsParams) -> str:
        """Get weakness details."""
        try:
            weakness = self.knowledge_base.get_weakness(params.weakness_id)

            if weakness is None:
                return self._wrap_response(f"Weakness {params.weakness_id} not found.")

            return self._wrap_response(json.dumps(weakness, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"weakness {params.weakness_id} retrieval")
            )


class GetMitigationDetailsParams(ToolParams):
    """Parameters for get_mitigation_details tool."""

    mitigation_id: str = Field(description="The mitigation ID (e.g., DFM-1001)", min_length=1)


class GetMitigationDetailsTool(SolveItBaseTool[GetMitigationDetailsParams]):
    """Tool to retrieve details for a specific SOLVE-IT mitigation."""

    name = "get_mitigation_details"
    description = (
        "Retrieve details for a mitigation by its DFM-XXXX ID. "
        "The 'name' field is the primary description of the recommended action. "
        "Use get_weaknesses_for_mitigation or get_techniques_for_mitigation to understand "
        "which weaknesses and techniques this mitigation addresses."
    )
    Params = GetMitigationDetailsParams

    async def invoke(self, params: GetMitigationDetailsParams) -> str:
        """Get mitigation details."""
        try:
            mitigation = self.knowledge_base.get_mitigation(params.mitigation_id)

            if mitigation is None:
                return self._wrap_response(f"Mitigation {params.mitigation_id} not found.")

            return self._wrap_response(json.dumps(mitigation, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"mitigation {params.mitigation_id} retrieval")
            )


class GetCitationParams(ToolParams):
    """Parameters for get_citation tool."""

    citation_id: str = Field(description="The citation ID (e.g., DFCite-1115)", min_length=1)


class GetCitationTool(SolveItBaseTool[GetCitationParams]):
    """Tool to resolve a citation ID to full bibliographic text."""

    name = "get_citation"
    description = (
        "Resolve a DFCite-XXXX citation ID to its full bibliographic reference text. "
        "Technique and weakness responses contain DFCite-XXXX IDs in their 'references' field — "
        "call this to get the actual source title, authors, and publication details. "
        "Use this when a user asks about the evidence or sources behind a technique or weakness."
    )
    Params = GetCitationParams

    async def invoke(self, params: GetCitationParams) -> str:
        """Get citation display text."""
        try:
            text = self.knowledge_base.get_citation_display_text(params.citation_id)
            return self._wrap_response(
                json.dumps({"id": params.citation_id, "reference": text}, indent=2)
            )

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"citation {params.citation_id} retrieval")
            )


class ResolveInlineCitationsParams(ToolParams):
    """Parameters for resolve_inline_citations tool."""

    text: str = Field(
        description=(
            "Text containing [DFCite-XXXX] citation markers to resolve. "
            "Each marker is replaced with a Harvard-style inline citation."
        ),
        min_length=1,
    )


class ResolveInlineCitationsTool(SolveItBaseTool[ResolveInlineCitationsParams]):
    """Tool to replace [DFCite-XXXX] markers with full Harvard-style citations."""

    name = "resolve_inline_citations"
    description = (
        "Replace [DFCite-XXXX] citation markers in text with full Harvard-style citations. "
        "Technique and weakness descriptions often contain [DFCite-XXXX] markers — "
        "call this to expand them into readable references in one step. "
        "More efficient than calling get_citation for each marker individually."
    )
    Params = ResolveInlineCitationsParams

    async def invoke(self, params: ResolveInlineCitationsParams) -> str:
        """Resolve inline citations in text."""
        try:
            resolved = self.knowledge_base.resolve_inline_citations(params.text)
            return json.dumps({"resolved_text": resolved}, indent=2)

        except Exception as e:
            return self.handle_knowledge_base_error(e, "inline citation resolution")


class GetMitigationsForTechniqueParams(ToolParams):
    """Parameters for get_mitigations_for_technique tool."""

    technique_id: str = Field(description="The technique ID (e.g., DFT-1001)", min_length=1)


class GetMitigationsForTechniqueTool(SolveItBaseTool[GetMitigationsForTechniqueParams]):
    """Tool to retrieve all mitigations for a technique in one step."""

    name = "get_mitigations_for_technique"
    description = (
        "Get all mitigations for a technique in one call, skipping the weakness intermediary. "
        "Shortcut for the technique → weaknesses → mitigations traversal. "
        "Use this when you want to know how to address limitations of a technique "
        "without needing to inspect individual weaknesses first."
    )
    Params = GetMitigationsForTechniqueParams

    async def invoke(self, params: GetMitigationsForTechniqueParams) -> str:
        """Get mitigations for technique via weakness traversal."""
        try:
            mitigation_ids = self.knowledge_base.get_mit_list_for_technique(params.technique_id)
            return json.dumps(
                {"technique_id": params.technique_id, "mitigations": mitigation_ids}, indent=2
            )

        except Exception as e:
            return self.handle_knowledge_base_error(
                e, f"mitigations for technique {params.technique_id}"
            )


class GetWeaknessesForTechniqueParams(ToolParams):
    """Parameters for get_weaknesses_for_technique tool."""

    technique_id: str = Field(description="The technique ID (e.g., DFT-1001)", min_length=1)


class GetWeaknessesForTechniqueTool(SolveItBaseTool[GetWeaknessesForTechniqueParams]):
    """Tool to retrieve all weaknesses associated with a specific technique."""

    name = "get_weaknesses_for_technique"
    description = (
        "Get all weaknesses for a technique (DFT-XXXX) with full details in one call. "
        "More efficient than calling get_weakness_details for each DFW-XXXX ID from get_technique_details. "
        "Use this to answer 'what can go wrong with this technique?'"
    )
    Params = GetWeaknessesForTechniqueParams

    async def invoke(self, params: GetWeaknessesForTechniqueParams) -> str:
        """Get weaknesses for a technique."""
        try:
            weaknesses = self.knowledge_base.get_weaknesses_for_technique(params.technique_id)

            return self._wrap_response(json.dumps(weaknesses, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"weaknesses for technique {params.technique_id}"
                )
            )


class GetMitigationsForWeaknessParams(ToolParams):
    """Parameters for get_mitigations_for_weakness tool."""

    weakness_id: str = Field(description="The weakness ID (e.g., DFW-1001)", min_length=1)


class GetMitigationsForWeaknessTool(SolveItBaseTool[GetMitigationsForWeaknessParams]):
    """Tool to retrieve all mitigations associated with a specific weakness."""

    name = "get_mitigations_for_weakness"
    description = (
        "Get all mitigations for a weakness (DFW-XXXX) with full details in one call. "
        "More efficient than resolving each DFM-XXXX ID from get_weakness_details individually. "
        "Use this to answer 'how can this weakness be addressed?'"
    )
    Params = GetMitigationsForWeaknessParams

    async def invoke(self, params: GetMitigationsForWeaknessParams) -> str:
        """Get mitigations for a weakness."""
        try:
            mitigations = self.knowledge_base.get_mitigations_for_weakness(params.weakness_id)

            return self._wrap_response(json.dumps(mitigations, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"mitigations for weakness {params.weakness_id}"
                )
            )


# =============================================================================
# Reverse Relationships
# =============================================================================


class GetTechniquesForWeaknessParams(ToolParams):
    """Parameters for get_techniques_for_weakness tool."""

    weakness_id: str = Field(description="The weakness ID (e.g., DFW-1001)", min_length=1)


class GetTechniquesForWeaknessTool(SolveItBaseTool[GetTechniquesForWeaknessParams]):
    """Tool to retrieve all techniques that reference a specific weakness."""

    name = "get_techniques_for_weakness"
    description = (
        "Find all techniques that can exhibit a specific weakness (DFW-XXXX). "
        "Use this for reverse lookup — e.g. 'which techniques are affected by this limitation?' "
        "Complements get_weaknesses_for_technique (forward direction)."
    )
    Params = GetTechniquesForWeaknessParams

    async def invoke(self, params: GetTechniquesForWeaknessParams) -> str:
        """Get techniques that reference a weakness."""
        try:
            techniques = self.knowledge_base.get_techniques_for_weakness(params.weakness_id)

            return self._wrap_response(json.dumps(techniques, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"techniques for weakness {params.weakness_id}")
            )


class GetWeaknessesForMitigationParams(ToolParams):
    """Parameters for get_weaknesses_for_mitigation tool."""

    mitigation_id: str = Field(description="The mitigation ID (e.g., DFM-1001)", min_length=1)


class GetWeaknessesForMitigationTool(SolveItBaseTool[GetWeaknessesForMitigationParams]):
    """Tool to retrieve all weaknesses that reference a specific mitigation."""

    name = "get_weaknesses_for_mitigation"
    description = (
        "Find all weaknesses that a mitigation (DFM-XXXX) addresses. "
        "Use this for reverse lookup — e.g. 'which weaknesses does this control fix?' "
        "Complements get_mitigations_for_weakness (forward direction)."
    )
    Params = GetWeaknessesForMitigationParams

    async def invoke(self, params: GetWeaknessesForMitigationParams) -> str:
        """Get weaknesses that reference a mitigation."""
        try:
            weaknesses = self.knowledge_base.get_weaknesses_for_mitigation(params.mitigation_id)

            return self._wrap_response(json.dumps(weaknesses, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"weaknesses for mitigation {params.mitigation_id}"
                )
            )


class GetTechniquesForMitigationParams(ToolParams):
    """Parameters for get_techniques_for_mitigation tool."""

    mitigation_id: str = Field(description="The mitigation ID (e.g., DFM-1001)", min_length=1)


class GetTechniquesForMitigationTool(SolveItBaseTool[GetTechniquesForMitigationParams]):
    """Tool to retrieve all techniques that reference a specific mitigation (through weaknesses)."""

    name = "get_techniques_for_mitigation"
    description = (
        "Find all techniques indirectly linked to a mitigation (DFM-XXXX) via their shared weaknesses. "
        "Use this to understand the scope of impact of a control — "
        "e.g. 'which techniques benefit from applying this mitigation?'"
    )
    Params = GetTechniquesForMitigationParams

    async def invoke(self, params: GetTechniquesForMitigationParams) -> str:
        """Get techniques that reference a mitigation."""
        try:
            techniques = self.knowledge_base.get_techniques_for_mitigation(params.mitigation_id)

            return self._wrap_response(json.dumps(techniques, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"techniques for mitigation {params.mitigation_id}"
                )
            )


# =============================================================================
# Objective / Mapping Tools
# =============================================================================


class ListObjectivesParams(ToolParams):
    """Parameters for list_objectives tool."""

    pass


class ListObjectivesTool(SolveItBaseTool[ListObjectivesParams]):
    """Tool to list all objectives from the current mapping."""

    name = "list_objectives"
    description = (
        "List all investigation objectives (workflow phases) from the currently loaded mapping. "
        "Objectives group techniques by investigation goal — e.g. 'Acquire data', 'Preserve digital evidence'. "
        "Use get_techniques_for_objective to get the techniques under a specific objective. "
        "Use load_objective_mapping to switch between frameworks (solve-it, carrier, dfrws)."
    )
    Params = ListObjectivesParams

    async def invoke(self, params: ListObjectivesParams) -> str:
        """List all objectives."""
        try:
            objectives = self.knowledge_base.list_objectives()

            return self._wrap_response(json.dumps(objectives, indent=2))

        except Exception as e:
            return self._wrap_response(self.handle_knowledge_base_error(e, "objectives listing"))


class GetTechniquesForObjectiveParams(ToolParams):
    """Parameters for get_techniques_for_objective tool."""

    objective_name: str = Field(
        description="The exact name of the objective (e.g., 'Acquire data')", min_length=1
    )


class GetTechniquesForObjectiveTool(SolveItBaseTool[GetTechniquesForObjectiveParams]):
    """Tool to retrieve all techniques for a specific objective."""

    name = "get_techniques_for_objective"
    description = (
        "Get all techniques belonging to a specific investigation objective (workflow phase). "
        "Use list_objectives first to get the exact objective names. "
        "Use this to answer 'what techniques are available for this phase of the investigation?'"
    )
    Params = GetTechniquesForObjectiveParams

    async def invoke(self, params: GetTechniquesForObjectiveParams) -> str:
        """Get techniques for an objective."""
        try:
            techniques = self.knowledge_base.get_techniques_for_objective(params.objective_name)

            return self._wrap_response(json.dumps(techniques, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"techniques for objective {params.objective_name}"
                )
            )


class GetObjectivesForTechniqueParams(ToolParams):
    """Parameters for get_objectives_for_technique tool."""

    technique_id: str = Field(description="The technique ID (e.g., DFT-1001)", min_length=1)


class GetObjectivesForTechniqueTool(SolveItBaseTool[GetObjectivesForTechniqueParams]):
    """Tool to retrieve all objectives that contain a specific technique."""

    name = "get_objectives_for_technique"
    description = (
        "Find which investigation objectives (workflow phases) a technique belongs to. "
        "Use this for reverse lookup — e.g. 'at what stage of an investigation is this technique used?' "
        "Also handles subtechniques by returning the parent technique's objectives. "
        "Complements get_techniques_for_objective (forward direction)."
    )
    Params = GetObjectivesForTechniqueParams

    async def invoke(self, params: GetObjectivesForTechniqueParams) -> str:
        """Get objectives for a technique."""
        try:
            objectives = self.knowledge_base.get_objectives_for_technique(params.technique_id)

            return self._wrap_response(json.dumps(objectives, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(
                    e, f"objectives for technique {params.technique_id}"
                )
            )


class ListAvailableMappingsParams(ToolParams):
    """Parameters for list_available_mappings tool."""

    pass


class ListAvailableMappingsTool(SolveItBaseTool[ListAvailableMappingsParams]):
    """Tool to list all available objective mapping files."""

    name = "list_available_mappings"
    description = (
        "List all available objective mapping files. "
        "Each mapping organises the same techniques into different investigation frameworks: "
        "solve-it.json (default SOLVE-IT framework), carrier.json (carrier/network context), "
        "dfrws.json (DFRWS framework). Use load_objective_mapping to switch between them."
    )
    Params = ListAvailableMappingsParams

    async def invoke(self, params: ListAvailableMappingsParams) -> str:
        """List available mapping files."""
        try:
            mappings = self.knowledge_base.list_available_mappings()

            return self._wrap_response(json.dumps(mappings, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "available mappings listing")
            )


class LoadObjectiveMappingParams(ToolParams):
    """Parameters for load_objective_mapping tool."""

    filename: str = Field(
        description="Mapping filename to load (e.g., 'carrier.json', 'dfrws.json', 'solve-it.json')",
        min_length=1,
    )


class LoadObjectiveMappingTool(SolveItBaseTool[LoadObjectiveMappingParams]):
    """Tool to switch to a different objective mapping."""

    name = "load_objective_mapping"
    description = (
        "Switch to a different investigation framework mapping. "
        "Use list_available_mappings to see valid filenames. "
        "After loading, list_objectives and get_techniques_for_objective will reflect the new framework. "
        "Use this when the user asks about techniques in the context of a specific framework (carrier, dfrws)."
    )
    Params = LoadObjectiveMappingParams

    async def invoke(self, params: LoadObjectiveMappingParams) -> str:
        """Load a different objective mapping."""
        try:
            success = self.knowledge_base.load_objective_mapping(params.filename)

            if success:
                result = {
                    "success": True,
                    "message": f"Successfully loaded mapping: {params.filename}",
                    "current_mapping": params.filename,
                }
            else:
                result = {
                    "success": False,
                    "message": f"Failed to load mapping: {params.filename}",
                    "current_mapping": self.knowledge_base.current_mapping_name,
                }

            return self._wrap_response(json.dumps(result, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, f"loading mapping {params.filename}")
            )


# =============================================================================
# Bulk Retrieval Tools
# =============================================================================


class GetAllTechniquesWithNameAndIdParams(ToolParams):
    """Parameters for get_all_techniques_with_name_and_id tool."""

    pass


class GetAllTechniquesWithNameAndIdTool(SolveItBaseTool[GetAllTechniquesWithNameAndIdParams]):
    """Tool to retrieve all techniques with ID and name only."""

    name = "get_all_techniques_with_name_and_id"
    description = (
        "Get all techniques as a concise ID+name list (~180 entries). "
        "Use this to browse the full catalogue or find IDs before calling get_technique_details. "
        "Prefer search when you have keywords — this returns everything."
    )
    Params = GetAllTechniquesWithNameAndIdParams

    async def invoke(self, params: GetAllTechniquesWithNameAndIdParams) -> str:
        """Get all techniques with ID and name only."""
        try:
            techniques = self.knowledge_base.get_all_techniques_with_name_and_id()

            return self._wrap_response(json.dumps(techniques, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all techniques with name and ID")
            )


class GetAllWeaknessesWithNameAndIdParams(ToolParams):
    """Parameters for get_all_weaknesses_with_name_and_id tool."""

    pass


class GetAllWeaknessesWithNameAndIdTool(SolveItBaseTool[GetAllWeaknessesWithNameAndIdParams]):
    """Tool to retrieve all weaknesses with ID and name only."""

    name = "get_all_weaknesses_with_name_and_id"
    description = (
        "Get all weaknesses as a concise ID+name list. "
        "Use this to browse all known weaknesses or find IDs before calling get_weakness_details. "
        "Prefer search when you have keywords — this returns everything."
    )
    Params = GetAllWeaknessesWithNameAndIdParams

    async def invoke(self, params: GetAllWeaknessesWithNameAndIdParams) -> str:
        """Get all weaknesses with ID and name only."""
        try:
            weaknesses = self.knowledge_base.get_all_weaknesses_with_name_and_id()

            return self._wrap_response(json.dumps(weaknesses, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all weaknesses with name and ID")
            )


class GetAllMitigationsWithNameAndIdParams(ToolParams):
    """Parameters for get_all_mitigations_with_name_and_id tool."""

    pass


class GetAllMitigationsWithNameAndIdTool(SolveItBaseTool[GetAllMitigationsWithNameAndIdParams]):
    """Tool to retrieve all mitigations with ID and name only."""

    name = "get_all_mitigations_with_name_and_id"
    description = (
        "Get all mitigations as a concise ID+name list. "
        "Use this to browse all available mitigations or find IDs before calling get_mitigation_details. "
        "Prefer search when you have keywords — this returns everything."
    )
    Params = GetAllMitigationsWithNameAndIdParams

    async def invoke(self, params: GetAllMitigationsWithNameAndIdParams) -> str:
        """Get all mitigations with ID and name only."""
        try:
            mitigations = self.knowledge_base.get_all_mitigations_with_name_and_id()

            return self._wrap_response(json.dumps(mitigations, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all mitigations with name and ID")
            )


class GetAllTechniquesWithFullDetailParams(ToolParams):
    """Parameters for get_all_techniques_with_full_detail tool."""

    pass


class GetAllTechniquesWithFullDetailTool(SolveItBaseTool[GetAllTechniquesWithFullDetailParams]):
    """Tool to retrieve all techniques with complete details."""

    name = "get_all_techniques_with_full_detail"
    description = (
        "Get all techniques with complete details (large response — use sparingly). "
        "Only use this when you need the full dataset in one call. "
        "For targeted lookups use search + get_technique_details instead."
    )
    Params = GetAllTechniquesWithFullDetailParams

    async def invoke(self, params: GetAllTechniquesWithFullDetailParams) -> str:
        """Get all techniques with full details."""
        try:
            techniques = self.knowledge_base.get_all_techniques_with_full_detail()

            return self._wrap_response(json.dumps(techniques, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all techniques with full detail")
            )


class GetAllWeaknessesWithFullDetailParams(ToolParams):
    """Parameters for get_all_weaknesses_with_full_detail tool."""

    pass


class GetAllWeaknessesWithFullDetailTool(SolveItBaseTool[GetAllWeaknessesWithFullDetailParams]):
    """Tool to retrieve all weaknesses with complete details."""

    name = "get_all_weaknesses_with_full_detail"
    description = (
        "Get all weaknesses with complete details (large response — use sparingly). "
        "Only use this when you need the full dataset in one call. "
        "For targeted lookups use search + get_weakness_details instead."
    )
    Params = GetAllWeaknessesWithFullDetailParams

    async def invoke(self, params: GetAllWeaknessesWithFullDetailParams) -> str:
        """Get all weaknesses with full details."""
        try:
            weaknesses = self.knowledge_base.get_all_weaknesses_with_full_detail()

            return self._wrap_response(json.dumps(weaknesses, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all weaknesses with full detail")
            )


class GetAllMitigationsWithFullDetailParams(ToolParams):
    """Parameters for get_all_mitigations_with_full_detail tool."""

    pass


class GetAllMitigationsWithFullDetailTool(SolveItBaseTool[GetAllMitigationsWithFullDetailParams]):
    """Tool to retrieve all mitigations with complete details."""

    name = "get_all_mitigations_with_full_detail"
    description = (
        "Get all mitigations with complete details (large response — use sparingly). "
        "Only use this when you need the full dataset in one call. "
        "For targeted lookups use search + get_mitigation_details instead."
    )
    Params = GetAllMitigationsWithFullDetailParams

    async def invoke(self, params: GetAllMitigationsWithFullDetailParams) -> str:
        """Get all mitigations with full details."""
        try:
            mitigations = self.knowledge_base.get_all_mitigations_with_full_detail()

            return self._wrap_response(json.dumps(mitigations, indent=2))

        except Exception as e:
            return self._wrap_response(
                self.handle_knowledge_base_error(e, "all mitigations with full detail")
            )
