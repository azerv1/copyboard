# Copyboard — agent guide

Operational rules for any AI agent working in this repo. Full detail lives in the project docs:
[SPEC.md](SPEC.md) (what/why), [ARCHITECTURE.md](ARCHITECTURE.md) (how), [TASKS.md](TASKS.md)
(progress), [PLAN.md](PLAN.md) (phased plan).

> `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md` are **identical** — edit all three together.

## What this is

A cross-platform (Windows, Linux, macOS) tray app that shows a live view of recent clipboard clippings
(text, URL, path, image), built with PySide6.

## Architecture: Hexagonal (Ports & Adapters) — the one rule that matters

- **`copyboard/domain/` and `copyboard/application/` must never `import PySide6`** (or any adapter, or
  do OS I/O). They are pure business rules and talk to the outside world only through the `Protocol`
  ports in `domain/ports.py` (`Clock`, `ClipboardSource`, `ClipboardSink`, `ClippingVault`,
  `HistoryObserver`).
- **`copyboard/adapters/`** is the only place Qt / OS APIs live (one concrete class per technology).
- **`copyboard/__main__.py`** is the composition root — the only place that wires concrete adapters
  into the service.

This keeps the core reusable behind a future web front-end and unit-testable with fakes.

## Coding standards

- **Fully typed.** Every function/method annotates all params *and* return type. `mypy` runs with
  `disallow_untyped_defs` over **both `copyboard/` and `tests/`** — unannotated code fails the gate.
- **`ruff` clean** on source and tests.
- **Descriptive, intention-revealing names** for every function, method, and class — everywhere, not
  just tests. Prefer `check_if_clipboard_has_image()` over `check()`,
  `looks_like_filesystem_path()` over `is_path()`. Short idioms are fine only where context makes
  intent unambiguous (e.g. `Clock.now()`).
- **Class-per-concept**: many small, single-purpose classes over a few large ones.
- **File named after its dominant class**, lowercased with no separators: `ClippingHistory` →
  `clippinghistory.py`, `CopyboardService` → `copyboardservice.py`. Files holding several co-equal
  classes keep a conceptual name (`content.py`, `ports.py`, `config.py`).
- Keep changes surgical; reuse what's here; no speculative abstraction.

## Configuration

Settings load from `config.json` at the repo root via `copyboard/config_loading.py`
(`load_app_config_from_json`); missing/partial files fall back to defaults in `copyboard/config.py`.
Retention defaults to 30 items / 20 minutes; the viewer toggle hotkey defaults to **Ctrl+Shift+H**;
the theme defaults to **dark** (`dark` / `light` / `system`, toggled live from the tray).

## Commands (via uv)

```
uv sync                 # create .venv and install deps
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy .           # type-check (src + tests)
uv run pytest           # tests
uv run copyboard        # launch the app
```

## Git

**The user handles all git commits.** Do not run `git add` / `git commit` / `git push`.
