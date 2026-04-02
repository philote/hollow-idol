# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `hollow_idol/`. Use `config.py` for shared dataclasses, `mold_case.py` for geometry generation, `printers.py` for bed presets, `export.py` for STL/STEP export, and `__main__.py` for the CLI entry point. Keep experimental or source reference meshes in `models/`, visual notes in `docs/`, and generated solids in `output/`. Treat `output/` as build artefacts, not hand-edited source.

## Build, Test, and Development Commands
This repository currently runs as a plain Python module rather than an installed package.

```bash
python -m venv .venv
. .venv/bin/activate
pip install build123d pytest
python -m hollow_idol --printer generic-200 --out-dir output/test_run
python -m hollow_idol --step
pytest
```

`python -m hollow_idol` generates the six mold parts. Add `--step` when you need CAD interchange files in addition to STL output. Use a dedicated subdirectory under `output/` for each run to avoid overwriting prior exports.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, type hints on public functions, dataclasses for configuration, and small focused modules. Use `snake_case` for modules, functions, variables, and CLI flags. Keep geometry code incremental and readable; prefer explicit dimensions and comments only where the shape logic is hard to infer. Avoid refactoring proven geometry casually.

## Testing Guidelines
`tests/` is present but not populated yet. Add `pytest` tests as `tests/test_<feature>.py`, starting with config validation, CLI argument coverage, and export-path behavior. For geometry changes, pair automated checks with a manual review of exported parts in a slicer such as PrusaSlicer. Do not merge shape changes without verifying dimensions and mating features.

## Commit & Pull Request Guidelines
Recent commits use short, lowercase subjects such as `parameterized!` and `working basic parametric mold generator`. Keep commit titles brief and descriptive; imperative phrasing is preferred when possible. Pull requests should explain the geometry or workflow change, list the command used to verify it, and include screenshots or slicer captures when exported part shapes changed.

## Output & Configuration Notes
Printer constraints are defined in `hollow_idol/printers.py`. If you add presets or CLI parameters, update both the code and `README.md` so contributors can reproduce the same export workflow.
