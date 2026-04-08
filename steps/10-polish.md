# Step 10: Polish

## Goal
Final cleanup, documentation, and quality pass before merging `dev` into `main` for the first real release.

## Tasks

### 1. Update `pyproject.toml`
- Set `description` to the final value: `"Terminal progress bars via decorators"`.
- Add relevant classifiers:
  ```toml
  classifiers = [
      "Development Status :: 3 - Alpha",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Programming Language :: Python :: 3",
      "Programming Language :: Python :: 3.9",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
      "Topic :: Software Development :: Libraries",
      "Topic :: Terminals",
  ]
  ```
- Add `keywords = ["progress", "terminal", "decorator", "cli", "rich"]`.
- Confirm `readme = "README.md"` is set and `README.md` exists with meaningful content.

### 2. Update `README.md`
Write a user-facing README covering:
- What `timeo` does (one paragraph).
- Installation: `pip install timeo`.
- Basic usage example (`@timeo.track` + `timeo.iter()`).
- Learn mode example (`@timeo.track(learn=True)`).
- `timeo.live()` context manager example.
- A note on `pre-commit` and dev setup for contributors.

### 3. Add type stubs / `py.typed` marker
Create an empty `timeo/py.typed` file to signal that the package ships inline types (PEP 561):

```
timeo/py.typed
```

Add it to the package include list in `pyproject.toml` if needed.

### 4. Final pre-commit pass
Run `pre-commit run --all-files` and fix any remaining issues:
- ruff lint and format
- mypy type errors
- TOML/YAML validation

### 5. Final test run
Run `pytest -v` and confirm all tests pass cleanly.

### 6. Review `scripts/smoke_test.py`
Decide whether to keep the smoke test scripts in the repo (under `scripts/`) or remove them. If kept, ensure they are excluded from the built package distribution.

### 7. Merge `dev` → `main`
- Open a pull request from `dev` to `main` on GitHub.
- Ensure all CI checks pass.
- Merge the PR (this will trigger release-please on `main` for the next version bump).

## Acceptance Criteria
- `pytest -v` — all tests pass.
- `pre-commit run --all-files` — no errors.
- `uv build` — produces clean `.whl` and `.tar.gz` artifacts.
- `README.md` is complete and accurate.
- `timeo/py.typed` exists.
- `dev` is merged into `main` via a passing PR.
