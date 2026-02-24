# Repository Guidelines

## Project Structure & Module Organization
- `mini_muse/` contains the core Python package (ComfyUI client, prompt generation, batch image/video scripts).
- `prompts/` stores JSON prompt element/template libraries; files are named like `prompt_templates_*.json`.
- `workflows/` holds ComfyUI workflow JSONs (e.g., `sd3.5_large_turbo_upscale.json`).
- `tests/` contains test scripts; add new tests as new files (do not modify existing tests).
- `config/` holds `config.yaml` for defaults; outputs land in `stablediffusion/outputs/YYYYMMDD/` with CSV logs.

## Build, Test, and Development Commands
- `uv sync` installs dependencies into the project environment.
- `uv run python mini_muse/generate_images.py` runs a single image generation (expects ComfyUI running).
- `uv run python mini_muse/generate_images.py --count 10` runs batch generation.
- `uv run python mini_muse/generate_images.py --list-templates` lists template files.
- `uv run python tests/test_prompt_generator.py` runs a focused test script.
- `uv run pytest tests/test_ollama_prompt.py -v` runs pytest-based tests (Ollama required).

## Coding Style & Naming Conventions
- Python 4-space indentation; follow PEP 8 conventions.
- Use `snake_case` for variables/functions, `PascalCase` for classes.
- Keep prompt templates in JSON with clear `description` fields and `{placeholders}` matching element keys.

## Testing Guidelines
- Tests live in `tests/` and are invoked via `uv run`.
- Prefer targeted tests per feature; name files `test_<feature>.py`.
- Some tests require external services (ComfyUI, Ollama); document prerequisites in test headers.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative, and may be bilingual (e.g., “Add support for multiple template files”).
- PRs should include: a clear summary, list of commands run, and any required external services/configuration.
- Include sample outputs or logs when changing prompt templates or generation workflows.

## Configuration & Runtime Notes
- Always run scripts with `uv run` (project standard).
- ComfyUI server defaults to `127.0.0.1:15434`; verify `config/config.yaml` if changing.
- Output directories are date-partitioned; do not hardcode a dated path unless required.
