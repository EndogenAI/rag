"""Tests for benchmark_rag.py judge evaluation functions.

Tests cover the 5 new functions added in commits b8fb1d3, fc869ff, and b874658:
1. load_judge_template() — template loading, code fence extraction, error handling
2. run_preflight_checks() — 5 preflight signals computation
3. evaluate_with_judge() — score parsing, preflight injection, API fallback
4. generate_judge_prompts_file() — JSONL format, header comments, tier-2 inclusion
5. load_judge_responses() — response parsing, missing query ID validation
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import functions under test
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.benchmark_rag import (
    evaluate_with_judge,
    generate_judge_prompts_file,
    load_judge_responses,
    load_judge_template,
    run_preflight_checks,
)

# --- Fixtures ---


@pytest.fixture
def mock_template_content():
    """Valid judge prompt template with code fence."""
    return """# RAG Judge Prompt Template

## Template Body

```
Score this RAG answer on a 0-1 scale:

Question: {query}
Answer: {answer}

Rubric: {rubric}

Preflight Signals:
{preflight_signals}

Return only a score (0.0, 0.5, or 1.0) and brief reasoning.
```

## Rationale
This template externalizes the judge prompt.
"""


@pytest.fixture
def mock_malformed_template():
    """Template missing code fence."""
    return """# RAG Judge Prompt Template

This template has no code fence.
"""


@pytest.fixture
def test_case_basic():
    """Basic test case with entities and patterns."""
    return {
        "id": "t2-001",
        "query": "What is the programmatic-first principle?",
        "expected_entities": ["script", "automation"],
        "expected_patterns": ["done twice", "third time"],
        "judge_rubric": "Check accuracy and completeness.",
    }


@pytest.fixture
def test_case_no_expectations():
    """Test case with no expected entities or patterns."""
    return {
        "id": "t2-002",
        "query": "Describe the agent fleet.",
        "judge_rubric": "Check clarity.",
    }


# --- Tests for load_judge_template() ---


@pytest.mark.io
def test_load_judge_template_happy_path(mock_template_content):
    """load_judge_template extracts template body from code fence."""
    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        template = load_judge_template()

    assert "Score this RAG answer on a 0-1 scale:" in template
    assert "{query}" in template
    assert "{answer}" in template
    assert "{rubric}" in template
    assert "{preflight_signals}" in template
    # Verify code fence markers are NOT in the extracted template
    assert "```" not in template


@pytest.mark.io
def test_load_judge_template_missing_code_fence(mock_malformed_template):
    """load_judge_template raises ValueError if code fence is missing."""
    with patch("builtins.open", mock_open(read_data=mock_malformed_template)):
        with pytest.raises(ValueError, match="Could not extract template body"):
            load_judge_template()


@pytest.mark.io
def test_load_judge_template_file_not_found():
    """load_judge_template propagates FileNotFoundError if template missing."""
    with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
        with pytest.raises(FileNotFoundError):
            load_judge_template()


# --- Tests for run_preflight_checks() ---


def test_run_preflight_checks_all_signals_present(test_case_basic):
    """run_preflight_checks computes all 5 signals correctly."""
    answer = (
        "The programmatic-first principle means if a task is done twice interactively, "
        "the third time it should be a script. This ensures automation and reduces token burn. "
        "See AGENTS.md for details."
    )
    retrieved_chunks = ["agents.md", "manifesto.md"]

    signals = run_preflight_checks(answer, test_case_basic, retrieved_chunks)

    assert signals["entity_hit_rate"] == 1.0  # Both "script" and "automation" present
    assert signals["pattern_hit_rate"] == 1.0  # Both "done twice" and "third time" present
    assert signals["is_substantive"] is True  # >20 tokens
    assert signals["cites_source"] is True  # "AGENTS.md" present
    assert signals["has_chunks"] is True  # 2 chunks retrieved


def test_run_preflight_checks_partial_entities(test_case_basic):
    """run_preflight_checks computes partial entity hit rate."""
    answer = "Use a script to automate this task."
    retrieved_chunks = []

    signals = run_preflight_checks(answer, test_case_basic, retrieved_chunks)

    assert signals["entity_hit_rate"] == 0.5  # Only "script" present (1 of 2)
    assert signals["pattern_hit_rate"] == 0.0  # Neither pattern present
    assert signals["is_substantive"] is False  # <20 tokens
    assert signals["cites_source"] is False  # No citation patterns
    assert signals["has_chunks"] is False  # No chunks


def test_run_preflight_checks_no_expectations(test_case_no_expectations):
    """run_preflight_checks handles test cases with no expected entities/patterns."""
    answer = (
        "This is a substantive answer with enough tokens to clearly pass the minimum "
        "threshold check for substantiveness. See docs/guides/ for more details."
    )
    retrieved_chunks = ["guide.md"]

    signals = run_preflight_checks(answer, test_case_no_expectations, retrieved_chunks)

    assert signals["entity_hit_rate"] == 0.0  # No entities to check
    assert signals["pattern_hit_rate"] == 0.0  # No patterns to check
    assert signals["is_substantive"] is True  # >20 tokens
    assert signals["cites_source"] is True  # "docs/" present
    assert signals["has_chunks"] is True


def test_run_preflight_checks_substantiveness_threshold():
    """run_preflight_checks marks short answers as non-substantive."""
    test_case = {"id": "t2-003", "query": "Test"}
    answer_short = "Yes."  # 1 token
    answer_borderline = " ".join(["token"] * 19)  # 19 tokens
    answer_substantive = " ".join(["token"] * 20)  # 20 tokens

    signals_short = run_preflight_checks(answer_short, test_case, [])
    signals_borderline = run_preflight_checks(answer_borderline, test_case, [])
    signals_substantive = run_preflight_checks(answer_substantive, test_case, [])

    assert signals_short["is_substantive"] is False
    assert signals_borderline["is_substantive"] is False
    assert signals_substantive["is_substantive"] is True


def test_run_preflight_checks_source_citation_patterns():
    """run_preflight_checks detects various citation patterns."""
    test_case = {"id": "t2-004", "query": "Test"}

    # Each answer should trigger cites_source=True
    citation_examples = [
        "See file.md for details.",
        "Refer to docs/guides/workflow.md",
        "Check scripts/fetch_source.py",
        "Read AGENTS.md",
        "Consult MANIFESTO.md",
    ]

    for answer in citation_examples:
        signals = run_preflight_checks(answer, test_case, [])
        assert signals["cites_source"] is True, f"Failed for: {answer}"

    # Non-citation answer
    signals_no_cite = run_preflight_checks("This has no citations.", test_case, [])
    assert signals_no_cite["cites_source"] is False


# --- Tests for evaluate_with_judge() ---


def test_evaluate_with_judge_prompts_only_mode(test_case_basic, mock_template_content):
    """evaluate_with_judge returns prompt without calling judge when prompts_only=True."""
    answer = "The programmatic-first principle requires scripting repeated tasks."
    retrieved_chunks = ["agents.md"]

    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        result = evaluate_with_judge(
            answer=answer,
            test_case=test_case_basic,
            judge_model="ollama/phi3",
            retrieved_chunks=retrieved_chunks,
            prompts_only=True,
        )

    assert "judge_prompt" in result
    assert "preflight_signals" in result
    assert "overall_score" not in result  # No scoring in prompts-only mode
    assert test_case_basic["query"] in result["judge_prompt"]
    assert answer in result["judge_prompt"]


def test_evaluate_with_judge_copilot_response_mode(test_case_basic, mock_template_content):
    """evaluate_with_judge uses pre-evaluated judge_response when provided."""
    answer = "Test answer"
    judge_response = "Score: 0.8\nReasoning: Good coverage of key concepts."

    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        result = evaluate_with_judge(
            answer=answer,
            test_case=test_case_basic,
            judge_model="ollama/phi3",
            retrieved_chunks=[],
            judge_response=judge_response,
        )

    assert result["overall_score"] == 0.8
    assert "Good coverage" in result["judge_reasoning"]
    assert result["evaluation_method"] == "llm_judge"
    assert "preflight_signals" in result


def test_evaluate_with_judge_score_parsing_patterns(test_case_basic, mock_template_content):
    """evaluate_with_judge parses various score formats correctly."""
    score_variants = [
        ("Score: 1.0\nReasoning: Perfect.", 1.0),
        ("Score: 0.5\nReasoning: Partial.", 0.5),
        ("Score: 0.0\nReasoning: Wrong.", 0.0),
        ("Award 1.0 for this answer.", 1.0),
        ("Award 0.5 for partial credit.", 0.5),
        ("No match here", 0.0),  # Fallback to 0.0
    ]

    for judge_response, expected_score in score_variants:
        with patch("builtins.open", mock_open(read_data=mock_template_content)):
            result = evaluate_with_judge(
                answer="Test",
                test_case=test_case_basic,
                judge_model="ollama/phi3",
                judge_response=judge_response,
            )
        assert result["overall_score"] == expected_score, f"Failed for: {judge_response}"


@patch("scripts.benchmark_rag.litellm")
def test_evaluate_with_judge_api_call(mock_litellm, test_case_basic, mock_template_content):
    """evaluate_with_judge calls litellm.completion when judge_response not provided."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Score: 0.9\nReasoning: Excellent answer."
    mock_litellm.completion.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        result = evaluate_with_judge(
            answer="Test answer",
            test_case=test_case_basic,
            judge_model="ollama/phi3",
            retrieved_chunks=[],
        )

    mock_litellm.completion.assert_called_once()
    assert result["overall_score"] == 0.9
    assert "Excellent" in result["judge_reasoning"]


@patch("scripts.benchmark_rag.litellm", None)
@patch("scripts.benchmark_rag.evaluate_response")
def test_evaluate_with_judge_fallback_no_litellm(mock_evaluate_response, test_case_basic, mock_template_content):
    """evaluate_with_judge falls back to evaluate_response when litellm not installed."""
    mock_evaluate_response.return_value = {"overall_score": 0.5, "evaluation_method": "pattern_matching"}

    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        result = evaluate_with_judge(
            answer="Test",
            test_case=test_case_basic,
            judge_model="ollama/phi3",
        )

    mock_evaluate_response.assert_called_once_with("Test", test_case_basic, judge_model=None)
    assert result["overall_score"] == 0.5


@patch("scripts.benchmark_rag.litellm")
@patch("scripts.benchmark_rag.evaluate_response")
def test_evaluate_with_judge_fallback_on_api_error(
    mock_evaluate_response, mock_litellm, test_case_basic, mock_template_content
):
    """evaluate_with_judge falls back to evaluate_response when API call fails."""
    mock_litellm.completion.side_effect = Exception("API timeout")
    mock_evaluate_response.return_value = {"overall_score": 0.5, "evaluation_method": "pattern_matching"}

    with patch("builtins.open", mock_open(read_data=mock_template_content)):
        result = evaluate_with_judge(
            answer="Test",
            test_case=test_case_basic,
            judge_model="ollama/phi3",
        )

    mock_evaluate_response.assert_called_once()
    assert result["overall_score"] == 0.5


# --- Tests for generate_judge_prompts_file() ---


@pytest.mark.io
@patch("scripts.benchmark_rag.yaml.dump")
@patch("scripts.benchmark_rag.load_judge_template")
@patch("scripts.benchmark_rag.run_rag_answer")
def test_generate_judge_prompts_file_multiple_test_cases(mock_run_rag, mock_load_template, mock_yaml_dump, tmp_path):
    """generate_judge_prompts_file handles multiple test cases correctly."""
    test_cases = [
        {"id": "t2-001", "query": "Query 1", "judge_rubric": "Rubric 1"},
        {"id": "t2-002", "query": "Query 2", "judge_rubric": "Rubric 2"},
        {"id": "t2-003", "query": "Query 3", "judge_rubric": "Rubric 3"},
    ]
    mock_run_rag.return_value = {"answer": "Test answer", "retrieval": {"sources": []}}
    mock_load_template.return_value = (
        "Score this RAG answer on a 0-1 scale:\n\n"
        "Question: {query}\nAnswer: {answer}\n\n"
        "Rubric: {rubric}\n\nPreflight Signals:\n{preflight_signals}\n\n"
        "Return only a score (0.0, 0.5, or 1.0) and brief reasoning."
    )
    mock_yaml_dump.return_value = "entity_hit_rate: 0.0\n"

    with patch("scripts.benchmark_rag.REPO_ROOT", tmp_path):
        prompts_file = generate_judge_prompts_file(
            test_cases=test_cases,
            model="ollama/phi3",
            top_k=5,
        )

    content = prompts_file.read_text()
    lines = [ln for ln in content.split("\n") if ln and not ln.startswith("#")]
    assert len(lines) == 3

    # Verify all query IDs present
    query_ids = [json.loads(ln)["query_id"] for ln in lines]
    assert query_ids == ["t2-001", "t2-002", "t2-003"]


@pytest.mark.io
@patch("scripts.benchmark_rag.run_rag_answer")
def test_generate_judge_prompts_file_template_fallback(mock_run_rag, tmp_path):
    """generate_judge_prompts_file uses inline prompt if template load fails."""
    mock_run_rag.return_value = {"answer": "Test answer", "retrieval": {"sources": []}}
    test_case = {"id": "t2-001", "query": "Test query", "judge_rubric": "Test rubric"}

    with patch("scripts.benchmark_rag.REPO_ROOT", tmp_path):
        # Simulate template load failure
        with patch("scripts.benchmark_rag.load_judge_template", side_effect=Exception("Template error")):
            prompts_file = generate_judge_prompts_file(
                test_cases=[test_case],
                model="ollama/phi3",
                top_k=5,
            )

    # Verify file created with inline prompt fallback
    content = prompts_file.read_text()
    lines = [ln for ln in content.split("\n") if ln and not ln.startswith("#")]
    entry = json.loads(lines[0])
    assert "Score this RAG answer on a 0-1 scale:" in entry["judge_prompt"]
    assert "Question: Test query" in entry["judge_prompt"]


# --- Tests for load_judge_responses() ---


@pytest.mark.io
def test_load_judge_responses_happy_path(tmp_path):
    """load_judge_responses loads responses correctly from JSONL."""
    responses_file = tmp_path / "judge-responses-test.jsonl"
    responses_file.write_text(
        '{"query_id": "t2-001", "judge_response": "Score: 1.0\\nReasoning: Perfect."}\n'
        '{"query_id": "t2-002", "judge_response": "Score: 0.5\\nReasoning: Partial."}\n'
    )

    responses = load_judge_responses(responses_file, expected_query_ids=["t2-001", "t2-002"])

    assert len(responses) == 2
    assert responses["t2-001"] == "Score: 1.0\nReasoning: Perfect."
    assert responses["t2-002"] == "Score: 0.5\nReasoning: Partial."


@pytest.mark.io
def test_load_judge_responses_skips_comments_and_empty_lines(tmp_path):
    """load_judge_responses ignores comment lines and blank lines."""
    responses_file = tmp_path / "judge-responses-test.jsonl"
    responses_file.write_text(
        "# This is a comment\n"
        "\n"
        '{"query_id": "t2-001", "judge_response": "Score: 1.0\\nReasoning: Good."}\n'
        "# Another comment\n"
        "\n"
        '{"query_id": "t2-002", "judge_response": "Score: 0.5\\nReasoning: OK."}\n'
    )

    responses = load_judge_responses(responses_file, expected_query_ids=["t2-001", "t2-002"])

    assert len(responses) == 2
    assert "t2-001" in responses
    assert "t2-002" in responses


@pytest.mark.io
def test_load_judge_responses_missing_query_ids(tmp_path):
    """load_judge_responses raises ValueError when expected query IDs are missing."""
    responses_file = tmp_path / "judge-responses-test.jsonl"
    responses_file.write_text('{"query_id": "t2-001", "judge_response": "Score: 1.0\\nReasoning: Good."}\n')

    with pytest.raises(ValueError, match="Missing responses for query IDs: \\['t2-002', 't2-003'\\]"):
        load_judge_responses(responses_file, expected_query_ids=["t2-001", "t2-002", "t2-003"])


@pytest.mark.io
def test_load_judge_responses_malformed_json_warning(tmp_path, capsys):
    """load_judge_responses skips malformed JSON lines with warning."""
    responses_file = tmp_path / "judge-responses-test.jsonl"
    responses_file.write_text(
        '{"query_id": "t2-001", "judge_response": "Score: 1.0\\nReasoning: Good."}\n'
        "Malformed line without JSON\n"
        '{"query_id": "t2-002", "judge_response": "Score: 0.5\\nReasoning: OK."}\n'
        '{"query_id": "t2-003"}\n'  # Missing judge_response field
    )

    responses = load_judge_responses(responses_file, expected_query_ids=["t2-001", "t2-002"])

    # Verify valid responses loaded
    assert len(responses) == 2
    assert "t2-001" in responses
    assert "t2-002" in responses

    # Verify warnings printed
    captured = capsys.readouterr()
    assert "WARNING: Skipping malformed response line" in captured.err


@pytest.mark.io
def test_load_judge_responses_file_not_found():
    """load_judge_responses propagates FileNotFoundError if response file missing."""
    with pytest.raises(FileNotFoundError):
        load_judge_responses(Path("/nonexistent/file.jsonl"), expected_query_ids=["t2-001"])
