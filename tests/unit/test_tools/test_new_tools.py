"""Unit tests for GetCitationTool, GetObjectivesForTechniqueTool, and SearchTool OR logic."""

import json
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from tools.solveit_tools import (
    GetCitationParams,
    GetCitationTool,
    GetObjectivesForTechniqueParams,
    GetObjectivesForTechniqueTool,
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


class TestSearchToolOrLogic:
    """Test SearchTool with search_logic='OR'."""

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

            result = await tool.invoke(params)
            tool.knowledge_base.search.assert_called_once_with(
                keywords="memory",
                item_types=None,
                search_logic="AND",
            )
