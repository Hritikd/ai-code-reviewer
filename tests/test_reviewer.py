import json
import pytest
from ai_code_reviewer.reviewer import ReviewResult, ReviewSummary, Issue, _parse_response, _build_user_prompt
from ai_code_reviewer.formatter import format_review, _filter_issues


class TestParseResponse:
    def test_valid_json_response(self):
        response = json.dumps({"summary": {"overall_quality": "good", "score": 7,
            "strengths": ["Clean code"], "improvements": ["Add tests"]},
            "issues": [{"line": 10, "severity": "high", "category": "bug",
            "title": "Null pointer", "description": "Variable could be None",
            "suggestion": "Add a None check"}]})
        result = _parse_response(response)
        assert result.summary.score == 7
        assert len(result.issues) == 1
        assert result.issues[0].severity == "high"

    def test_json_wrapped_in_markdown(self):
        response = '```json\n{"summary": {"overall_quality": "good", "score": 8, "strengths": [], "improvements": []}, "issues": []}\n```'
        result = _parse_response(response)
        assert result.summary.score == 8

    def test_invalid_json_returns_fallback(self):
        result = _parse_response("This is not JSON at all!")
        assert result.summary.overall_quality == "unknown"
        assert result.summary.score == 0

    def test_empty_issues_list(self):
        response = json.dumps({"summary": {"overall_quality": "excellent", "score": 10,
            "strengths": ["Perfect"], "improvements": []}, "issues": []})
        result = _parse_response(response)
        assert len(result.issues) == 0


class TestBuildUserPrompt:
    def test_includes_filename(self):
        assert "test.py" in _build_user_prompt("x = 1", "Python", "test.py")

    def test_includes_language(self):
        assert "Python" in _build_user_prompt("x = 1", "Python", "test.py")

    def test_includes_line_numbers(self):
        prompt = _build_user_prompt("line1\nline2\nline3", "Python", "test.py")
        assert "   1 |" in prompt


class TestFilterIssues:
    def _make_review(self, severities):
        issues = [Issue(line=i, severity=s, category="bug", title=f"Issue {i}",
                  description="", suggestion="") for i, s in enumerate(severities, 1)]
        return ReviewResult(summary=ReviewSummary(overall_quality="fair", score=5), issues=issues)

    def test_filter_high_only(self):
        filtered = _filter_issues(self._make_review(["low", "medium", "high"]), "high")
        assert len(filtered) == 1

    def test_filter_medium_and_above(self):
        filtered = _filter_issues(self._make_review(["low", "medium", "high"]), "medium")
        assert len(filtered) == 2


class TestFormatReview:
    def _make_sample_review(self):
        return ReviewResult(
            summary=ReviewSummary(overall_quality="fair", score=5,
                strengths=["Good naming"], improvements=["Add error handling"]),
            issues=[Issue(line=10, severity="high", category="security",
                title="SQL Injection", description="User input in SQL query",
                suggestion="Use parameterized queries")])

    def test_json_format_is_valid_json(self):
        data = json.loads(format_review(self._make_sample_review(), format_type="json", filename="test.py"))
        assert data["file"] == "test.py"
        assert data["summary"]["score"] == 5

    def test_markdown_format_has_headers(self):
        output = format_review(self._make_sample_review(), format_type="markdown", filename="test.py")
        assert "# Code Review: test.py" in output
