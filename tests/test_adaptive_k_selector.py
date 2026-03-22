"""
Tests for scripts/adaptive_k_selector.py
"""

import pytest
from scripts.adaptive_k_selector import extract_parameter_count, select_k


def test_extract_parameter_count():
    # Happy paths
    assert extract_parameter_count("qwen2.5:1.5b") == 1.5
    assert extract_parameter_count("llama3.1:8b") == 8.0
    assert extract_parameter_count("smollm:360m") == 0.36
    assert extract_parameter_count("deepseek-v3:671b") == 671.0
    
    # Case sensitivity and weird strings
    assert extract_parameter_count("GRANITE-3.0:2B") == 2.0
    assert extract_parameter_count("no-params-here") == 0.0
    assert extract_parameter_count("") == 0.0


def test_select_k_tiers():
    # Tier 1: < 1.5B -> k=20
    assert select_k(0.5) == 20
    assert select_k(1.4) == 20
    
    # Tier 2: 1.5B - 8B -> k=10
    assert select_k(1.5) == 10
    assert select_k(3.0) == 10
    assert select_k(8.0) == 10
    
    # Tier 3: > 8B -> k=5
    assert select_k(8.1) == 5
    assert select_k(70.0) == 5
    
    # Edge cases
    assert select_k(0.0) == 10  # Fallback


def test_main_cli(capsys):
    from scripts.adaptive_k_selector import main
    import sys
    from unittest.mock import patch

    # Test with model name
    with patch.object(sys, 'argv', ['adaptive_k_selector.py', 'qwen2.5:1.5b']):
        main()
        captured = capsys.readouterr()
        assert captured.out.strip() == "10"

    # Test with explicit params
    with patch.object(sys, 'argv', ['adaptive_k_selector.py', '--params', '0.5']):
        main()
        captured = capsys.readouterr()
        assert captured.out.strip() == "20"

    # Test with help (will trigger sys.exit)
    with patch.object(sys, 'argv', ['adaptive_k_selector.py']):
        with pytest.raises(SystemExit):
            main()


def test_boundary_behavior():
    # Testing boundaries strictly
    # 1.499 should be Tier 1
    assert select_k(1.499) == 20
    # 1.5 should be Tier 2
    assert select_k(1.5) == 10
    
    # 8.0 should be Tier 2
    assert select_k(8.0) == 10
    # 8.001 should be Tier 3
    assert select_k(8.001) == 5
