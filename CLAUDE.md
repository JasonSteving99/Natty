# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

- Build library: `bazel build :<target> --action_env=LLM_API_KEY=<your_gemini_api_key>`
- Run binary: `bazel run :<target> --action_env=LLM_API_KEY=<your_gemini_api_key>`
- Generate requirements.txt: `bazel run //:generate_requirements_txt`
- Create virtual environment: `bazel run //:create_venv`
- Sync virtual environment: `bazel run //:sync_venv`

## Code Style Guidelines

- Use Python 3.10+ syntax (e.g., `list[str]` instead of `List[str]`)
- Use union syntax in Python types (e.g., `str | None` instead of `Optional[str]`)
- Add proper type hints to all functions and variables
- Include docstrings for all functions and classes
- Add appropriate error handling
- Follow PEP 8 style guidelines
- Ensure code is well-structured and follows best practices
- When implementing Natty components, focus on clear, concise behavior descriptions
- For markdown descriptions, be specific about the expected functionality
- Follow existing patterns when working with Bazel rules