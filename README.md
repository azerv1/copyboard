# Copyboard

A small  tray app that shows a live view of your recent
clipboard clippings so you can glance back and re-copy anything you copied earlier, not just the last item.

## Install & run

Requires [uv](https://docs.astral.sh/uv/) and Python 3.10+.

```
uv sync            # create .venv and install dependencies
uv run copyboard   # launch the tray app
```

The app lives in the **system tray**. Click the tray icon or press the global hotkey
(**Ctrl+Shift+H** by default) to show/hide the viewer. In the viewer, **Copy** puts an item back on
the clipboard and **Delete** removes it.
**Edit config…**.

## Configuration

Settings load from `config.json` at the repo root (missing/partial files fall back to defaults):

```json
{
  "retention": { "max_items": 30, "max_age_minutes": 20 },
  "hotkey": { "toggle_viewer_hotkey": "ctrl+shift+h" },
  "theme": "dark"
}
```

Retention keeps at most `max_items` clippings **and** drops anything older than `max_age_minutes`.
`theme` is `dark` (default), `light`, or `system` (follow the OS)

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
