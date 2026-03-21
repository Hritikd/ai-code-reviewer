import json
from dataclasses import asdict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ai_code_reviewer.reviewer import ReviewResult

console = Console()

SEVERITY_COLORS = {"high": "red", "medium": "yellow", "low": "blue"}
SEVERITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🔵"}
CATEGORY_EMOJI = {"bug": "🐛", "security": "🔒", "performance": "⚡", "style": "🎨", "best-practice": "📐"}
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def _filter_issues(review, min_severity):
    min_level = SEVERITY_ORDER.get(min_severity, 0)
    return [i for i in review.issues if SEVERITY_ORDER.get(i.severity, 0) >= min_level]


def _format_pretty(review, min_severity, filename):
    output = Console(record=True)
    score = review.summary.score
    quality = review.summary.overall_quality
    score_color = "green" if score >= 8 else "yellow" if score >= 5 else "red"

    summary_text = Text()
    summary_text.append("Score: ", style="bold")
    summary_text.append(f"{score}/10", style=f"bold {score_color}")
    summary_text.append("  •  Quality: ", style="bold")
    summary_text.append(f"{quality.upper()}", style=f"bold {score_color}")
    output.print(Panel(summary_text, title=f"📋 Review: {filename}", border_style="cyan"))

    if review.summary.strengths:
        output.print("\n[bold green]✅ Strengths:[/bold green]")
        for s in review.summary.strengths:
            output.print(f"   • {s}")
    if review.summary.improvements:
        output.print("\n[bold yellow]💡 Suggested Improvements:[/bold yellow]")
        for imp in review.summary.improvements:
            output.print(f"   • {imp}")

    filtered = _filter_issues(review, min_severity)
    if not filtered:
        output.print(f"\n[green]No issues found at severity ≥ {min_severity}! 🎉[/green]\n")
        return output.export_text()

    output.print(f"\n[bold]Found {len(filtered)} issue(s):[/bold]\n")
    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Line", justify="right", style="cyan", width=6)
    table.add_column("Severity", justify="center", width=10)
    table.add_column("Category", width=14)
    table.add_column("Issue", min_width=40)

    for issue in filtered:
        sev_emoji = SEVERITY_EMOJI.get(issue.severity, "⚪")
        sev_color = SEVERITY_COLORS.get(issue.severity, "white")
        cat_emoji = CATEGORY_EMOJI.get(issue.category, "📌")
        table.add_row(str(issue.line), f"{sev_emoji} [{sev_color}]{issue.severity}[/{sev_color}]",
                       f"{cat_emoji} {issue.category}", issue.title)
    output.print(table)

    output.print("\n[bold]📝 Details:[/bold]\n")
    for i, issue in enumerate(filtered, 1):
        sev_color = SEVERITY_COLORS.get(issue.severity, "white")
        cat_emoji = CATEGORY_EMOJI.get(issue.category, "📌")
        detail = Text()
        detail.append(f"Line {issue.line}: ", style="bold cyan")
        detail.append(f"{issue.title}\n\n", style="bold")
        detail.append(f"{issue.description}\n\n", style="dim")
        detail.append("💡 Fix: ", style="bold green")
        detail.append(f"{issue.suggestion}")
        output.print(Panel(detail, title=f"{cat_emoji} Issue {i} [{issue.severity.upper()}]",
                           border_style=sev_color))
    return output.export_text()


def _format_json(review, min_severity, filename):
    filtered = _filter_issues(review, min_severity)
    output = {"file": filename, "summary": asdict(review.summary),
              "issues": [asdict(i) for i in filtered], "total_issues": len(filtered)}
    return json.dumps(output, indent=2)


def _format_markdown(review, min_severity, filename):
    lines = [f"# Code Review: {filename}\n",
             f"**Score:** {review.summary.score}/10 | **Quality:** {review.summary.overall_quality.upper()}\n"]
    if review.summary.strengths:
        lines.append("## ✅ Strengths\n")
        lines.extend(f"- {s}" for s in review.summary.strengths)
        lines.append("")
    if review.summary.improvements:
        lines.append("## 💡 Improvements\n")
        lines.extend(f"- {imp}" for imp in review.summary.improvements)
        lines.append("")
    filtered = _filter_issues(review, min_severity)
    if not filtered:
        lines.append(f"\n> No issues found at severity ≥ {min_severity} 🎉\n")
        return "\n".join(lines)
    lines.append(f"## 🔍 Issues ({len(filtered)})\n")
    lines.append("| Line | Severity | Category | Issue |")
    lines.append("|------|----------|----------|-------|")
    for issue in filtered:
        sev_emoji = SEVERITY_EMOJI.get(issue.severity, "⚪")
        lines.append(f"| {issue.line} | {sev_emoji} {issue.severity} | {issue.category} | {issue.title} |")
    lines.append("\n### Details\n")
    for i, issue in enumerate(filtered, 1):
        lines.append(f"#### {i}. {issue.title} (Line {issue.line})")
        lines.append(f"**Severity:** {issue.severity} | **Category:** {issue.category}\n")
        lines.append(f"{issue.description}\n")
        lines.append(f"**Suggestion:** {issue.suggestion}\n")
        lines.append("---\n")
    return "\n".join(lines)


def format_review(review, format_type="pretty", min_severity="low", filename="unknown"):
    formatters = {"pretty": _format_pretty, "json": _format_json, "markdown": _format_markdown}
    return formatters.get(format_type, _format_pretty)(review, min_severity, filename)
