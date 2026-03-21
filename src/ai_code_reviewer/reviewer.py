import json
import os
from dataclasses import dataclass, field

from openai import OpenAI, APIError, AuthenticationError, RateLimitError


@dataclass
class Issue:
    line: int
    severity: str
    category: str
    title: str
    description: str
    suggestion: str


@dataclass
class ReviewSummary:
    overall_quality: str
    score: int
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    summary: ReviewSummary
    issues: list[Issue] = field(default_factory=list)
    raw_response: str = ""


SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review.
Your job is to find bugs, security issues, performance problems, and style issues.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation outside JSON).
The JSON must follow this exact schema:

{
  "summary": {
    "overall_quality": "poor|fair|good|excellent",
    "score": <1-10>,
    "strengths": ["strength 1", "strength 2"],
    "improvements": ["improvement 1", "improvement 2"]
  },
  "issues": [
    {
      "line": <line_number>,
      "severity": "low|medium|high",
      "category": "bug|security|performance|style|best-practice",
      "title": "Short issue title",
      "description": "Detailed explanation of the issue",
      "suggestion": "How to fix it, with code example if applicable"
    }
  ]
}

SEVERITY GUIDE:
- high: Bugs that will cause crashes, security vulnerabilities, data loss
- medium: Performance issues, potential bugs, missing error handling
- low: Style issues, naming conventions, minor improvements

RULES:
- Be specific: reference exact line numbers
- Be constructive: always suggest how to fix each issue
- Be honest: if the code is good, say so (don't invent fake issues)
- Include at least one strength even in poor code
- Return an empty issues array if the code has no problems
- Respond ONLY with the JSON object, nothing else"""


def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise OSError(
            "OPENAI_API_KEY environment variable is not set.\n"
            "Get your API key from: https://platform.openai.com/api-keys\n"
            "Then run: export OPENAI_API_KEY='your-key-here'"
        )
    return OpenAI(api_key=api_key)


def _build_user_prompt(code: str, language: str, filename: str) -> str:
    numbered_lines = []
    for i, line in enumerate(code.splitlines(), start=1):
        numbered_lines.append(f"{i:4d} | {line}")
    numbered_code = "\n".join(numbered_lines)
    return f"""Review the following {language} file: {filename}
```{language.lower()}
{numbered_code}
```

Provide a thorough code review following the JSON schema specified in your instructions."""


def _parse_response(response_text: str) -> ReviewResult:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return ReviewResult(
            summary=ReviewSummary(overall_quality="unknown", score=0,
                                  strengths=[], improvements=["Could not parse AI response"]),
            issues=[], raw_response=response_text,
        )
    summary_data = data.get("summary", {})
    summary = ReviewSummary(
        overall_quality=summary_data.get("overall_quality", "unknown"),
        score=summary_data.get("score", 0),
        strengths=summary_data.get("strengths", []),
        improvements=summary_data.get("improvements", []),
    )
    issues = []
    for issue_data in data.get("issues", []):
        issues.append(Issue(
            line=issue_data.get("line", 0), severity=issue_data.get("severity", "low"),
            category=issue_data.get("category", "style"), title=issue_data.get("title", "Unknown"),
            description=issue_data.get("description", ""), suggestion=issue_data.get("suggestion", ""),
        ))
    return ReviewResult(summary=summary, issues=issues, raw_response=response_text)


def review_code(code: str, language: str, filename: str,
                model: str = "gpt-4o", max_tokens: int = 4096) -> ReviewResult:
    client = _get_client()
    user_prompt = _build_user_prompt(code, language, filename)
    try:
        response = client.chat.completions.create(
            model=model, max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        response_text = response.choices[0].message.content
        return _parse_response(response_text)
    except AuthenticationError:
        raise RuntimeError("Invalid API key. Check your OPENAI_API_KEY.\n"
                           "Get a new key at: https://platform.openai.com/api-keys")
    except RateLimitError:
        raise RuntimeError("Rate limit exceeded. Wait a moment and try again.")
    except APIError as e:
        raise RuntimeError(f"API error: {e.message}")
