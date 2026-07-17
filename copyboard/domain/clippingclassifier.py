"""Turn a raw clipboard snapshot into the most specific :class:`Clipping` subclass.

Detection is pure and syntactic — no filesystem or network I/O — so it is fully deterministic and
unit-testable. Rules are applied in priority order: image, then url, path, json, markdown, command,
and finally plain text as the fallback.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from copyboard.domain.clipping import (
    Clipping,
    CommandClipping,
    ImageClipping,
    JsonClipping,
    MarkdownClipping,
    PathClipping,
    TextClipping,
    UrlClipping,
)
from copyboard.domain.content import ImagePayload, RawClipboardData
from copyboard.domain.ports import ClippingVault, Clock

_URL_SCHEMES = frozenset({"http", "https", "ftp", "ftps"})

_KNOWN_COMMAND_WORDS = frozenset(
    {
        "git",
        "npm",
        "npx",
        "pnpm",
        "yarn",
        "uv",
        "uvx",
        "pip",
        "pipx",
        "python",
        "python3",
        "py",
        "node",
        "deno",
        "bun",
        "go",
        "cargo",
        "rustc",
        "make",
        "cmake",
        "docker",
        "podman",
        "kubectl",
        "helm",
        "terraform",
        "ansible",
        "ssh",
        "scp",
        "rsync",
        "curl",
        "wget",
        "cd",
        "ls",
        "cat",
        "echo",
        "cp",
        "mv",
        "rm",
        "mkdir",
        "touch",
        "grep",
        "sed",
        "awk",
        "find",
        "chmod",
        "chown",
        "tar",
        "zip",
        "unzip",
        "sudo",
        "apt",
        "apt-get",
        "brew",
        "dnf",
        "yum",
        "pacman",
        "winget",
        "choco",
        "scoop",
        "systemctl",
        "service",
    }
)
_COMMAND_PROMPT_PREFIXES = ("$ ", "> ", "# ", "PS ")

_MARKDOWN_STRONG_PATTERNS = (
    re.compile(r"^#{1,6}\s+\S", re.MULTILINE),  # heading
    re.compile(r"^```", re.MULTILINE),  # fenced code block
    re.compile(r"^>\s+\S", re.MULTILINE),  # blockquote
    re.compile(r"\[[^\]]+\]\([^)]+\)"),  # inline link
    re.compile(r"\*\*[^*]+\*\*"),  # bold
)
_MARKDOWN_LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S", re.MULTILINE)
_MIN_MARKDOWN_LIST_ITEMS = 2

_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")
_UNC_PATH_PATTERN = re.compile(r"^(?:\\\\|//)[^\\/]")
_POSIX_ABSOLUTE_PATTERN = re.compile(r"^/[^/]")
_HOME_PATH_PATTERN = re.compile(r"^~[\\/]")


class UrlDetector:
    """Recognises text that is a URL with a supported scheme."""

    def looks_like_url(self, text: str) -> bool:
        candidate = text.strip()
        if not candidate or any(character.isspace() for character in candidate):
            return False
        parsed = urlparse(candidate)
        return parsed.scheme.lower() in _URL_SCHEMES and bool(parsed.netloc)


class PathDetector:
    """Recognises text that is a filesystem path, by syntax only (Windows, UNC, or POSIX)."""

    def looks_like_filesystem_path(self, text: str) -> bool:
        candidate = text.strip()
        if not candidate or "\n" in candidate:
            return False
        return any(
            pattern.search(candidate) is not None
            for pattern in (
                _WINDOWS_DRIVE_PATTERN,
                _UNC_PATH_PATTERN,
                _POSIX_ABSOLUTE_PATTERN,
                _HOME_PATH_PATTERN,
            )
        )


class JsonDetector:
    """Recognises text that parses as a JSON object or array."""

    def looks_like_json(self, text: str) -> bool:
        candidate = text.strip()
        if not (candidate.startswith(("{", "[")) and candidate.endswith(("}", "]"))):
            return False
        try:
            json.loads(candidate)
        except ValueError:
            return False
        return True


class MarkdownDetector:
    """Recognises text carrying Markdown structure (headings, lists, code fences, links…)."""

    def looks_like_markdown(self, text: str) -> bool:
        if any(pattern.search(text) is not None for pattern in _MARKDOWN_STRONG_PATTERNS):
            return True
        list_items = len(_MARKDOWN_LIST_ITEM_PATTERN.findall(text))
        return list_items >= _MIN_MARKDOWN_LIST_ITEMS


class CommandDetector:
    """Recognises text whose first line looks like a shell / CLI command."""

    def looks_like_command(self, text: str) -> bool:
        first_line = self._first_nonempty_line(text)
        if first_line is None:
            return False
        if first_line.startswith(_COMMAND_PROMPT_PREFIXES):
            return True
        first_word = first_line.split(maxsplit=1)[0]
        return first_word in _KNOWN_COMMAND_WORDS

    def _first_nonempty_line(self, text: str) -> str | None:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
        return None


class ClippingClassifier:
    """Builds the most specific clipping for a raw clipboard snapshot.

    Image bytes are handed to the injected :class:`ClippingVault`; the resulting temp-file path is
    stored on the :class:`ImageClipping`. The injected :class:`Clock` stamps ``created_at``.
    """

    def __init__(
        self,
        vault: ClippingVault,
        clock: Clock,
        url_detector: UrlDetector | None = None,
        path_detector: PathDetector | None = None,
        json_detector: JsonDetector | None = None,
        markdown_detector: MarkdownDetector | None = None,
        command_detector: CommandDetector | None = None,
    ) -> None:
        self._vault = vault
        self._clock = clock
        self._url_detector = url_detector or UrlDetector()
        self._path_detector = path_detector or PathDetector()
        self._json_detector = json_detector or JsonDetector()
        self._markdown_detector = markdown_detector or MarkdownDetector()
        self._command_detector = command_detector or CommandDetector()

    def classify_clipboard_content(self, raw: RawClipboardData) -> Clipping | None:
        if raw.image is not None:
            return self._build_image_clipping(raw.image)
        if raw.text:
            return self._build_text_clipping(raw.text)
        return None

    def _build_image_clipping(self, image: ImagePayload) -> ImageClipping:
        suffix = f".{image.image_format.lstrip('.')}"
        stored_path = self._vault.store_image_bytes(image.data, suffix=suffix)
        return ImageClipping(
            created_at=self._clock.now(),
            size_bytes=image.size_bytes,
            path=stored_path,
            image_format=image.image_format,
        )

    def _build_text_clipping(self, text: str) -> Clipping:
        created_at = self._clock.now()
        size_bytes = len(text.encode("utf-8"))
        if self._url_detector.looks_like_url(text):
            return UrlClipping(created_at=created_at, size_bytes=size_bytes, text=text)
        if self._path_detector.looks_like_filesystem_path(text):
            path = Path(text.strip())
            return PathClipping(created_at=created_at, size_bytes=size_bytes, path=path)
        if self._json_detector.looks_like_json(text):
            return JsonClipping(created_at=created_at, size_bytes=size_bytes, text=text)
        if self._markdown_detector.looks_like_markdown(text):
            return MarkdownClipping(created_at=created_at, size_bytes=size_bytes, text=text)
        if self._command_detector.looks_like_command(text):
            return CommandClipping(created_at=created_at, size_bytes=size_bytes, text=text)
        return TextClipping(created_at=created_at, size_bytes=size_bytes, text=text)
