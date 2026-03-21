import argparse
import sys
from pathlib import Path

from ai_code_reviewer.reviewer import review_code
from ai_code_reviewer.formatter import format_review


def create_parser():
    parser = argparse.ArgumentParser(
        prog="ai-review",
        description="AI-powered code review using GPT-4o. Get structured feedback on any code file.",
        epilog="Example: ai-review myfile.py --severity medium --output json",
    )
    parser.add_argument("file", type=str, help="Path to the code file to review")
    parser.add_argument("--severity", choices=["low", "medium", "high"], default="medium",
                        help="Minimum severity level to report (default: medium)")
    parser.add_argument("--output", choices=["pretty", "json", "markdown"], default="pretty",
                        help="Output format (default: pretty terminal output)")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="Model to use (default: gpt-4o). Try gpt-4o-mini for cheaper reviews.")
    parser.add_argument("--max-tokens", type=int, default=4096,
                        help="Maximum tokens in the model's response (default: 4096)")
    return parser


def validate_file(file_path: str) -> Path:
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)
    if not path.is_file():
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)
    if path.stat().st_size == 0:
        print(f"Error: File is empty: {file_path}", file=sys.stderr)
        sys.exit(1)
    max_size_kb = 100
    if path.stat().st_size > max_size_kb * 1024:
        print(f"Error: File too large ({path.stat().st_size // 1024}KB). Max: {max_size_kb}KB",
              file=sys.stderr)
        sys.exit(1)
    return path


def main():
    parser = create_parser()
    args = parser.parse_args()
    file_path = validate_file(args.file)

    try:
        code_content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"Error: Cannot read file (not a text file?): {args.file}", file=sys.stderr)
        sys.exit(1)

    extension_to_language = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React JSX", ".tsx": "React TSX", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".cpp": "C++",
        ".c": "C", ".cs": "C#", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    }
    language = extension_to_language.get(file_path.suffix, "Unknown")

    print(f"\n🔍 Reviewing {file_path.name} ({language})...\n")

    try:
        review_result = review_code(
            code=code_content, language=language, filename=file_path.name,
            model=args.model, max_tokens=args.max_tokens,
        )
    except Exception as e:
        print(f"Error during review: {e}", file=sys.stderr)
        sys.exit(1)

    output = format_review(
        review=review_result, format_type=args.output,
        min_severity=args.severity, filename=file_path.name,
    )
    print(output)


if __name__ == "__main__":
    main()
