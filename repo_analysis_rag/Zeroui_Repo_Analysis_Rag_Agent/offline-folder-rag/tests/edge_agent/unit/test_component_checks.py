import sys
from pathlib import Path
from unittest.mock import patch
import pytest

def _setup_path():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

_setup_path()

from edge_agent.app.tools import doctor

def test_ollama_ok_returns_boolean():
    """Test ollama_ok returns boolean based on Ollama status."""
    # Currently check_ollama is a placeholder returning True
    assert isinstance(doctor.check_ollama(), bool)
    assert doctor.check_ollama() is True

@patch("shutil.which")
def test_ripgrep_ok_returns_boolean(mock_which):
    """Test ripgrep_ok returns boolean based on ripgrep availability."""
    # Test found
    mock_which.return_value = "/usr/bin/rg"
    assert doctor.check_ripgrep() is True
    
    # Test not found
    mock_which.return_value = None
    assert doctor.check_ripgrep() is False

def test_chroma_ok_returns_boolean():
    """Test chroma_ok returns boolean based on Chroma accessibility."""
    # Currently check_chroma is a placeholder returning True
    assert isinstance(doctor.check_chroma(), bool)
    assert doctor.check_chroma() is True

def test_component_checks_edge_cases():
    """Test edge cases for component checks."""
    # For now, since they are placeholders, we just ensure they don't crash
    # and return the expected default values.
    assert doctor.check_ollama() is True
    assert doctor.check_chroma() is True
