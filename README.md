# 🔍 AI Code Reviewer

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GPT-4o](https://img.shields.io/badge/Powered%20by-GPT--4o-green.svg)](https://openai.com/)

**AI-powered code review from your terminal.** Get structured, actionable feedback on any code file using GPT-4o — with severity ratings, line-specific issues, and fix suggestions.

## What it does

Pass any code file to `ai-review` and get back:

- **Overall score** (1-10) with quality rating
- **Strengths** — what you're doing well
- **Issues** — bugs, security flaws, performance problems, style issues
- **Fix suggestions** — concrete code suggestions for each issue

Output as **pretty terminal UI**, **JSON** (for pipelines), or **Markdown** (for PRs).

## Quick start
```bash
git clone https://github.com/Hritikd/ai-code-reviewer.git
cd ai-code-reviewer
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export OPENAI_API_KEY="your-key-here"
ai-review examples/sample_buggy.py
```

## Usage
```bash
ai-review myfile.py                        # basic review
ai-review myfile.py --severity high        # only high-severity issues
ai-review myfile.py --output json          # JSON output for pipelines
ai-review myfile.py --output markdown      # Markdown for GitHub PRs
ai-review myfile.py --model gpt-4o-mini   # cheaper model
```

## Project structure
```
ai-code-reviewer/
├── src/ai_code_reviewer/
│   ├── cli.py           # CLI entry point (argparse)
│   ├── reviewer.py      # OpenAI API integration
│   └── formatter.py     # Output formatting (Rich/JSON/Markdown)
├── tests/               # 11 tests covering parsing, filtering, formatting
├── examples/
│   └── sample_buggy.py  # Try reviewing this!
└── pyproject.toml       # Project config & dependencies
```

## What I learned building this

- **Structured outputs from LLMs** — crafting prompts that return valid JSON consistently
- **OpenAI JSON mode** — `response_format={"type": "json_object"}` guarantees valid JSON
- **CLI architecture** — argparse, entry points, exit codes
- **Python packaging** — pyproject.toml, virtual environments, pip install
- **Testing** — pytest for validating LLM output parsing and formatting logic

## Cost

~$0.01 per review with GPT-4o. Under $0.001 with gpt-4o-mini.

## License

MIT

---

*Built by [Hritik](https://github.com/Hritikd)*
