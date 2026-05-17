"""Unit tests for new tools: citation, inline citations, mitigations shortcut, search options."""

import json
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from tools.solveit_tools import (
    GetCitationParams,
    GetCitationTool,
    GetMitigationsForTechniqueParams,
    GetMitigationsForTechniqueTool,
    GetObjectivesForTechniqueParams,
    GetObjectivesForTechniqueTool,
    ResolveInlineCitationsParams,
    ResolveInlineCitationsTool,
    SearchParams,
    SearchTool,
)


class TestGetCitationTool:
    """Test GetCitationTool functionality."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        tool = GetCitationTool()

        assert tool.name == "get_citation"
        assert "citation" in tool.description.lower()
        assert tool.Params == GetCitationParams

    @pytest.mark.asyncio
    async def test_successful_citation_retrieval(self, mock_solve_it_environment):
        """Test happy path: citation text is returned."""
        with (
            patch.object(GetCitationTool, "_resolve_data_path"),
            patch.object(GetCitationTool, "_init_knowledge_base"),
        ):
            tool = GetCitationTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = GetCitationParams(citation_id="DFCite-1115")
            result = await tool.invoke(params)

            data = json.loads(result)
            assert data["id"] == "DFCite-1115"
            assert data["reference"] == "Test Author (2024). Test Title. Test Journal."
            tool.knowledge_base.get_citation_display_text.assert_called_once_with("DFCite-1115")

    @pytest.mark.asyncio
    async def test_citation_not_found(self, mock_solve_it_environment):
        """Test that a not-found exception is handled gracefully."""
        with (
            patch.object(GetCitationTool, "_resolve_data_path"),
            patch.object(GetCitationTool, "_init_knowledge_base"),
        ):
            tool = GetCitationTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]
            tool.knowledge_base.get_citation_display_text.side_effect = Exception(
                "Citation not found"
            )

            params = GetCitationParams(citation_id="DFCite-9999")
            result = await tool.invoke(params)

            assert "not found" in result.lower()

    def test_citation_params_validation(self):
        """Test that empty citation_id raises ValidationError."""
        with pytest.raises(ValidationError):
            GetCitationParams(citation_id="")

        with pytest.raises(ValidationError):
            GetCitationParams(citation_id="   ")

        with pytest.raises(ValidationError):
            GetCitationParams()

        # Valid case
        params = GetCitationParams(citation_id="DFCite-1115")
        assert params.citation_id == "DFCite-1115"


class TestGetObjectivesForTechniqueTool:
    """Test GetObjectivesForTechniqueTool functionality."""

    def test_tool_metadata(self):
        """Test tool metadata is correct."""
        tool = GetObjectivesForTechniqueTool()

        assert tool.name == "get_objectives_for_technique"
        assert "objective" in tool.description.lower()
        assert tool.Params == GetObjectivesForTechniqueParams

    @pytest.mark.asyncio
    async def test_successful_objectives_retrieval(self, mock_solve_it_environment):
        """Test happy path: list of objectives is returned."""
        with (
            patch.object(GetObjectivesForTechniqueTool, "_resolve_data_path"),
            patch.object(GetObjectivesForTechniqueTool, "_init_knowledge_base"),
        ):
            tool = GetObjectivesForTechniqueTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = GetObjectivesForTechniqueParams(technique_id="DFT-1001")
            result = await tool.invoke(params)

            data = json.loads(result)
            assert isinstance(data, list)
            assert "Test Objective 1" in data
            assert "Test Objective 2" in data
            tool.knowledge_base.get_objectives_for_technique.assert_called_once_with("DFT-1001")

    @pytest.mark.asyncio
    async def test_unknown_technique(self, mock_solve_it_environment):
        """Test that an error for an unknown technique is handled gracefully."""
        with (
            patch.object(GetObjectivesForTechniqueTool, "_resolve_data_path"),
            patch.object(GetObjectivesForTechniqueTool, "_init_knowledge_base"),
        ):
            tool = GetObjectivesForTechniqueTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]
            tool.knowledge_base.get_objectives_for_technique.side_effect = Exception(
                "Technique not found"
            )

            params = GetObjectivesForTechniqueParams(technique_id="DFT-9999")
            result = await tool.invoke(params)

            assert "not found" in result.lower()

    def test_objectives_for_technique_params_validation(self):
        """Test that empty technique_id raises ValidationError."""
        with pytest.raises(ValidationError):
            GetObjectivesForTechniqueParams(technique_id="")

        with pytest.raises(ValidationError):
            GetObjectivesForTechniqueParams(technique_id="   ")

        with pytest.raises(ValidationError):
            GetObjectivesForTechniqueParams()

        # Valid case
        params = GetObjectivesForTechniqueParams(technique_id="DFT-1001")
        assert params.technique_id == "DFT-1001"


class TestResolveInlineCitationsTool:
    """Test ResolveInlineCitationsTool functionality."""

    def test_tool_metadata(self):
        tool = ResolveInlineCitationsTool()
        assert tool.name == "resolve_inline_citations"
        assert "citation" in tool.description.lower()
        assert tool.Params == ResolveInlineCitationsParams

    @pytest.mark.asyncio
    async def test_successful_resolution(self, mock_solve_it_environment):
        """Test that [DFCite-XXXX] markers are replaced."""
        with (
            patch.object(ResolveInlineCitationsTool, "_resolve_data_path"),
            patch.object(ResolveInlineCitationsTool, "_init_knowledge_base"),
        ):
            tool = ResolveInlineCitationsTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = ResolveInlineCitationsParams(
                text="Some text with [DFCite-1115] inline."
            )
            result = await tool.invoke(params)

            data = json.loads(result)
            assert "resolved_text" in data
            assert "[DFCite-" not in data["resolved_text"]
            tool.knowledge_base.resolve_inline_citations.assert_called_once_with(
                "Some text with [DFCite-1115] inline."
            )

    @pytest.mark.asyncio
    async def test_resolution_error_handled(self, mock_solve_it_environment):
        """Test that errors are handled gracefully."""
        with (
            patch.object(ResolveInlineCitationsTool, "_resolve_data_path"),
            patch.object(ResolveInlineCitationsTool, "_init_knowledge_base"),
        ):
            tool = ResolveInlineCitationsTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]
            tool.knowledge_base.resolve_inline_citations.side_effect = Exception("parse error")

            params = ResolveInlineCitationsParams(text="Text with [DFCite-9999].")
            result = await tool.invoke(params)

            assert "error" in result.lower()

    def test_params_validation(self):
        with pytest.raises(ValidationError):
            ResolveInlineCitationsParams(text="")
        with pytest.raises(ValidationError):
            ResolveInlineCitationsParams(text="   ")
        with pytest.raises(ValidationError):
            ResolveInlineCitationsParams()

        params = ResolveInlineCitationsParams(text="Valid text [DFCite-1115].")
        assert "DFCite-1115" in params.text


class TestGetMitigationsForTechniqueTool:
    """Test GetMitigationsForTechniqueTool functionality."""

    def test_tool_metadata(self):
        tool = GetMitigationsForTechniqueTool()
        assert tool.name == "get_mitigations_for_technique"
        assert "mitigation" in tool.description.lower()
        assert tool.Params == GetMitigationsForTechniqueParams

    @pytest.mark.asyncio
    async def test_successful_retrieval(self, mock_solve_it_environment):
        """Test happy path: mitigation IDs returned for a technique."""
        with (
            patch.object(GetMitigationsForTechniqueTool, "_resolve_data_path"),
            patch.object(GetMitigationsForTechniqueTool, "_init_knowledge_base"),
        ):
            tool = GetMitigationsForTechniqueTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = GetMitigationsForTechniqueParams(technique_id="DFT-1001")
            result = await tool.invoke(params)

            data = json.loads(result)
            assert data["technique_id"] == "DFT-1001"
            assert "DFM-1001" in data["mitigations"]
            assert "DFM-1002" in data["mitigations"]
            tool.knowledge_base.get_mit_list_for_technique.assert_called_once_with("DFT-1001")

    @pytest.mark.asyncio
    async def test_unknown_technique_handled(self, mock_solve_it_environment):
        """Test that unknown technique error is handled gracefully."""
        with (
            patch.object(GetMitigationsForTechniqueTool, "_resolve_data_path"),
            patch.object(GetMitigationsForTechniqueTool, "_init_knowledge_base"),
        ):
            tool = GetMitigationsForTechniqueTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]
            tool.knowledge_base.get_mit_list_for_technique.side_effect = Exception(
                "Technique not found"
            )

            params = GetMitigationsForTechniqueParams(technique_id="DFT-9999")
            result = await tool.invoke(params)

            assert "not found" in result.lower()

    def test_params_validation(self):
        with pytest.raises(ValidationError):
            GetMitigationsForTechniqueParams(technique_id="")
        with pytest.raises(ValidationError):
            GetMitigationsForTechniqueParams(technique_id="   ")
        with pytest.raises(ValidationError):
            GetMitigationsForTechniqueParams()

        params = GetMitigationsForTechniqueParams(technique_id="DFT-1001")
        assert params.technique_id == "DFT-1001"


class TestSearchToolOptions:
    """Test SearchTool search_logic and substring_match options."""

    @pytest.mark.asyncio
    async def test_search_with_or_logic(self, mock_solve_it_environment):
        """Test that OR logic is passed correctly to the knowledge base."""
        with (
            patch.object(SearchTool, "_resolve_data_path"),
            patch.object(SearchTool, "_init_knowledge_base"),
        ):
            tool = SearchTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = SearchParams(keywords="memory acquisition", search_logic="OR")
            result = await tool.invoke(params)

            data = json.loads(result)
            assert isinstance(data, dict)
            tool.knowledge_base.search.assert_called_once_with(
                keywords="memory acquisition",
                item_types=None,
                search_logic="OR",
                substring_match=False,
            )

    @pytest.mark.asyncio
    async def test_search_default_and_logic(self, mock_solve_it_environment):
        """Test that AND is the default search logic."""
        with (
            patch.object(SearchTool, "_resolve_data_path"),
            patch.object(SearchTool, "_init_knowledge_base"),
        ):
            tool = SearchTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = SearchParams(keywords="memory")
            assert params.search_logic == "AND"
            assert params.substring_match is False

            result = await tool.invoke(params)
            tool.knowledge_base.search.assert_called_once_with(
                keywords="memory",
                item_types=None,
                search_logic="AND",
                substring_match=False,
            )

    @pytest.mark.asyncio
    async def test_search_with_substring_match(self, mock_solve_it_environment):
        """Test that substring_match=True is passed to the knowledge base."""
        with (
            patch.object(SearchTool, "_resolve_data_path"),
            patch.object(SearchTool, "_init_knowledge_base"),
        ):
            tool = SearchTool()
            tool.knowledge_base = mock_solve_it_environment["knowledge_base"]

            params = SearchParams(keywords="mem", substring_match=True)
            result = await tool.invoke(params)

            data = json.loads(result)
            assert isinstance(data, dict)
            tool.knowledge_base.search.assert_called_once_with(
                keywords="mem",
                item_types=None,
                search_logic="AND",
                substring_match=True,
            )

    def test_search_params_defaults(self):
        """Test SearchParams defaults."""
        params = SearchParams(keywords="test")
        assert params.search_logic == "AND"
        assert params.substring_match is False
        assert params.item_types is None
