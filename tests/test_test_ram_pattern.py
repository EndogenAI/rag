"""Tests for scripts/test_ram_pattern.py

Covers:
- get_ram_gb: returns a positive float, delegates to psutil
- check_model_loaded: True when model tag in ollama ps stdout, False otherwise, False on timeout/not-found
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── dependency isolation ──────────────────────────────────────────────────────
# test_ram_pattern.py does a module-level: from rag_index import answer_query
# We inject a stub so the module can be imported in test context.
_mock_rag_index = MagicMock()
_mock_rag_index.answer_query = MagicMock(return_value={"ok": True, "answer": "stub"})
sys.modules.setdefault("rag_index", _mock_rag_index)

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── get_ram_gb ────────────────────────────────────────────────────────────────


def test_get_ram_gb_returns_positive_float():
    """get_ram_gb() returns a float > 0 derived from psutil.virtual_memory()."""
    from scripts.test_ram_pattern import get_ram_gb

    mock_mem = MagicMock()
    mock_mem.available = 8 * 1024**3  # 8 GB

    with patch("psutil.virtual_memory", return_value=mock_mem):
        result = get_ram_gb()

    assert isinstance(result, float)
    assert result == pytest.approx(8.0, abs=0.01)


def test_get_ram_gb_scales_bytes_to_gb():
    """Byte value is correctly converted: 16 GiB → ~16.0."""
    from scripts.test_ram_pattern import get_ram_gb

    mock_mem = MagicMock()
    mock_mem.available = 16 * 1024**3  # 16 GiB

    with patch("psutil.virtual_memory", return_value=mock_mem):
        result = get_ram_gb()

    assert result == pytest.approx(16.0, abs=0.01)


# ── check_model_loaded ────────────────────────────────────────────────────────


def test_check_model_loaded_returns_true_when_tag_in_output():
    """Returns True when the model tag (without ollama/ prefix) appears in ollama ps stdout."""
    from scripts.test_ram_pattern import check_model_loaded

    mock_result = MagicMock()
    mock_result.stdout = "phi3:mini   active\n"

    with patch("subprocess.run", return_value=mock_result):
        assert check_model_loaded("ollama/phi3:mini") is True


def test_check_model_loaded_returns_false_when_tag_absent():
    """Returns False when the model tag is not in ollama ps stdout."""
    from scripts.test_ram_pattern import check_model_loaded

    mock_result = MagicMock()
    mock_result.stdout = "qwen2.5:7b   active\n"

    with patch("subprocess.run", return_value=mock_result):
        assert check_model_loaded("ollama/phi3:mini") is False


def test_check_model_loaded_returns_false_on_timeout():
    """Returns False gracefully when subprocess.TimeoutExpired is raised."""
    from scripts.test_ram_pattern import check_model_loaded

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="ollama", timeout=5)):
        assert check_model_loaded("ollama/phi3:mini") is False


def test_check_model_loaded_returns_false_when_ollama_not_found():
    """Returns False gracefully when ollama binary is not installed (FileNotFoundError)."""
    from scripts.test_ram_pattern import check_model_loaded

    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert check_model_loaded("ollama/phi3:mini") is False


def test_check_model_loaded_strips_ollama_prefix():
    """The 'ollama/' prefix is stripped before checking ollama ps output."""
    from scripts.test_ram_pattern import check_model_loaded

    mock_result = MagicMock()
    # stdout contains the bare tag, not the prefixed form
    mock_result.stdout = "phi3:mini\n"

    with patch("subprocess.run", return_value=mock_result):
        result = check_model_loaded("ollama/phi3:mini")

    assert result is True
