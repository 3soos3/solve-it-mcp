"""Unit test configuration.

Patches SOLVE-IT data path resolution and knowledge base initialisation for
every unit test so that tools can be instantiated without real data on disk.
Tests that need a mock knowledge base use the mock_solve_it_environment
fixture from the top-level conftest.py.

Re-exports assert_error_response and validate_json_response so that tool test
files which do ``from conftest import ...`` resolve them correctly when pytest
is run from the repo root with tests/unit/ as the test path.
"""

from unittest.mock import patch

import pytest

from tools.solveit_base import SolveItBaseTool

# Re-export helpers that tool test files import via ``from conftest import …``
from tests.conftest import assert_error_response, validate_json_response

__all__ = ["assert_error_response", "validate_json_response"]


@pytest.fixture(autouse=True)
def patch_solveit_init(request):
    """Prevent tools from trying to resolve SOLVE-IT data paths during unit tests.

    Tests that exercise _resolve_data_path directly can opt out by marking
    themselves with ``@pytest.mark.no_patch_solveit_init``.
    """
    if request.node.get_closest_marker("no_patch_solveit_init"):
        yield
        return
    with (
        patch.object(SolveItBaseTool, "_resolve_data_path"),
        patch.object(SolveItBaseTool, "_init_knowledge_base"),
    ):
        yield
