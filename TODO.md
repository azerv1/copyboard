# TODO

## Manual test checklist (need a real desktop — can't be verified headlessly)

These exercise the OS clipboard / window manager, so they must be checked by running
`uv run copyboard` on Windows. Once confirmed, promote each into an automated integration/e2e
test where feasible.

- [ ] **Screenshot capture** — `Win+Shift+S` (and `PrintScreen`) puts a bitmap on the clipboard;
      it should appear as an image preview in the viewer. (Encode path is unit-tested in
      `tests/adapters/test_qtclipboard.py`; the real OS round-trip is not.)
- [ ] **No console duplicates** — copying a command from `cmd`/PowerShell inserts it **once**
      (was 4×). De-dup logic is unit-tested; confirm against the real multi-fire behaviour.
- [ ] **No browser duplicates** — copying text/a link from a browser inserts it **once** (was 2×).
- [ ] **Hotkey pops to front** — with the viewer open but behind another window, `Ctrl+Shift+H`
      raises it to the front (does not hide it). Pressing it again while it's frontmost hides it.
      (The hidden→front direction is unit-tested; focus-stealing is OS-dependent — if Windows
      refuses to raise, we may need a `SetForegroundWindow` workaround.)
- [ ] **Edit config** — tray → "Edit config…" opens `config.json` (seeding defaults if missing).
      Note: edits currently apply only after restarting the app.
- [ ] **Theme** — starts dark; tray → "Toggle light / dark" flips the whole window live (verify all
      widgets, including buttons and the timestamp, restyle cleanly in both directions).

## Backlog

- **Colour-code kinds in the viewer** (deferred from the "remove kinds from the UI" change): the
  domain still classifies url/path/text — later, style them (e.g. URL accent, red for commands,
  blue for `.py` paths) instead of showing a plain kind label.
- Live config reload (apply `config.json` edits without a restart).
