# Copyboard

A small **cross-platform** (Windows, Linux, macOS) tray app that shows a live view of your recent
clipboard clippings — text, URLs, paths, JSON, Markdown, shell commands, and images — so you can
glance back and re-copy anything you copied earlier, not just the last item.

## Why

The OS clipboard only remembers the *last* copied item. While working you copy many things in a row
— a screenshot, some text, a file path, a URL — and all but the last are lost. Copyboard keeps the
recent ones visible.

## Install & run

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```
uv sync            # create .venv and install dependencies
uv run copyboard   # launch the tray app
```

The app lives in the **system tray**. Click the tray icon or press the global hotkey
(**Ctrl+Shift+H** by default) to show/hide the viewer. In the viewer, **Copy** puts an item back on
the clipboard and **Delete** removes it.

## Configuration

Settings load from `config.json` at the repo root (missing/partial files fall back to defaults):

```json
{
  "retention": { "max_items": 30, "max_age_minutes": 20 },
  "hotkey": { "toggle_viewer_hotkey": "ctrl+shift+h" }
}
```

Retention keeps at most `max_items` clippings **and** drops anything older than `max_age_minutes`.

## How it works

- **In-memory** history (clears on exit). Clipboard **images** are written to the OS temp directory
  and referenced by path; **path** clippings reference the existing file; **text** stays in memory.
- Built with **PySide6** behind a **Hexagonal (Ports & Adapters)** architecture: the pure core
  (`copyboard/domain`, `copyboard/application`) never imports Qt, so it is fully unit-tested and could
  be re-fronted (e.g. as a web app) by swapping only the adapter layer. See
  [ARCHITECTURE.md](ARCHITECTURE.md).

Docs: [SPEC.md](SPEC.md) (scope) · [ARCHITECTURE.md](ARCHITECTURE.md) (design) ·
[TASKS.md](TASKS.md) (progress) · [PLAN.md](PLAN.md) (phased plan).

## Development

```
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy .           # type-check (src + tests, disallow untyped defs)
uv run pytest           # tests
```

## Platform notes

The global hotkey uses `pynput`, which needs **X11** on Linux (not native Wayland) and
**Accessibility permission** on macOS. If the hotkey can't bind, the app still runs — use the tray
icon to open the viewer.
