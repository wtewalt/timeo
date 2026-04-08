# Step 1: Package Scaffold

## Goal
Set up the `timeo` Python package structure and clean up the repo of placeholder files.

## Tasks

### 1. Remove placeholder files
- Delete `hello.py` from the repo root — it is a leftover from the project template and is no longer needed.

### 2. Create the package directory and module files
Create the following files (empty for now, they will be implemented in later steps):

```
timeo/
├── __init__.py
├── decorator.py
├── manager.py
└── task.py
```

### 3. Update `pyproject.toml`
- Set `description` to a meaningful value: `"Terminal progress bars via decorators"`
- Confirm `rich` is listed as a dependency (it should already be present).
- Add `platformdirs` as a dependency — it will be needed for cross-platform cache path resolution in a later step.
- Set the package source to the `timeo/` directory if not already configured.

### 4. Stub out `timeo/__init__.py`
Add a module docstring describing the package. Do not export any symbols yet — that comes in a later step.

```python
"""
timeo — terminal progress bars via decorators.
"""
```

## Acceptance Criteria
- `uv sync` runs without errors.
- `python -c "import timeo"` succeeds without errors.
- `hello.py` no longer exists in the repo root.
- The `timeo/` directory contains `__init__.py`, `decorator.py`, `manager.py`, and `task.py`.
