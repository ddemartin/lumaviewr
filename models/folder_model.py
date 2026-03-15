"""Model representing an open folder and its image list."""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional


class SortKey(str, Enum):
    NAME      = "name"
    DATE      = "date"
    SIZE      = "size"
    EXTENSION = "ext"

from core.decoder_base import BaseDecoder
from core.decoder_pillow import PillowDecoder
from core.decoder_psd import PsdDecoder
from core.decoder_raw import RawDecoder
from core.decoder_fits import FitsDecoder
from core.decoder_heif import HeifDecoder
from core.decoder_svg import SvgDecoder
from models.image_model import ImageEntry

# All recognised extensions across registered decoders
_ALL_EXTENSIONS: frozenset[str] = frozenset(
    PillowDecoder.SUPPORTED_EXTENSIONS
    + PsdDecoder.SUPPORTED_EXTENSIONS
    + RawDecoder.SUPPORTED_EXTENSIONS
    + FitsDecoder.SUPPORTED_EXTENSIONS
    + HeifDecoder.SUPPORTED_EXTENSIONS
    + SvgDecoder.SUPPORTED_EXTENSIONS
)

_VIDEO_EXTENSIONS: frozenset[str] = frozenset((
    ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm", ".m4v", ".flv", ".mpeg", ".mpg",
))
_AUDIO_EXTENSIONS: frozenset[str] = frozenset((
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus",
))
_MEDIA_EXTENSIONS: frozenset[str] = _VIDEO_EXTENSIONS | _AUDIO_EXTENSIONS

_ALL_SUPPORTED: frozenset[str] = _ALL_EXTENSIONS | _MEDIA_EXTENSIONS


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in _ALL_SUPPORTED


class FolderModel:
    """
    Maintains the ordered list of images in a directory.

    Scanning is done synchronously; in a full implementation this would
    run on a background thread to avoid blocking the UI.
    """

    def __init__(self) -> None:
        self._folder: Optional[Path] = None
        self._entries: list[ImageEntry] = []
        self._current_index: int = -1
        self._sort_key: SortKey = SortKey.NAME
        self._sort_reverse: bool = False

    # ------------------------------------------------------------------ #
    # Sorting                                                              #
    # ------------------------------------------------------------------ #

    def set_sort(self, key: SortKey, reverse: bool) -> None:
        """Change sort order and re-sort the current entries in-place."""
        self._sort_key = key
        self._sort_reverse = reverse
        if not self._entries:
            return
        current_path = self.current.path if self.current else None
        dirs  = [e for e in self._entries if e.is_dir]
        files = [e for e in self._entries if not e.is_dir]
        files.sort(key=lambda e: self._file_sort_key(e.path), reverse=reverse)
        self._entries = dirs + files
        if current_path is not None:
            idx = self._index_of(current_path)
            self._current_index = idx if idx >= 0 else self._current_index

    def _file_sort_key(self, p: Path):
        if self._sort_key == SortKey.DATE:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0.0
        if self._sort_key == SortKey.SIZE:
            try:
                return p.stat().st_size
            except OSError:
                return 0
        if self._sort_key == SortKey.EXTENSION:
            return (p.suffix.lower(), p.name.lower())
        return p.name.lower()  # NAME (default)

    # ------------------------------------------------------------------ #
    # Folder management                                                    #
    # ------------------------------------------------------------------ #

    def load_folder(self, folder: Path) -> None:
        """Scan *folder* and populate the entry list (subdirs first, then files)."""
        self._folder = folder
        try:
            children = list(folder.iterdir())
        except PermissionError:
            children = []
        dirs = sorted(
            (
                p for p in children
                if p.is_dir()
                and not p.name.startswith(".")
                and not p.name.startswith("$")
            ),
            key=lambda p: p.name.lower(),
        )
        files = sorted(
            (p for p in children if p.is_file() and _is_supported(p)),
            key=self._file_sort_key,
            reverse=self._sort_reverse,
        )
        self._entries = (
            [ImageEntry(path=p, is_dir=True) for p in dirs]
            + [ImageEntry(path=p) for p in files]
        )
        # Start on the first file entry (skip leading dir entries)
        first_file = next((i for i, e in enumerate(self._entries) if not e.is_dir), -1)
        self._current_index = first_file

    def load_drives(self) -> None:
        """Populate entries with all available drives (Computer view)."""
        self._folder = None
        drives = [
            Path(f"{c}:\\")
            for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if Path(f"{c}:\\").exists()
        ] or [Path("/")]
        self._entries = [ImageEntry(path=d, is_dir=True) for d in drives]
        self._current_index = -1

    def load_folder_recursive(self, folder: Path) -> None:
        """Scan *folder* and all subdirectories; populate with files only (flat list)."""
        self._folder = folder
        files: list[Path] = []
        try:
            for root, dirs, fnames in os.walk(folder):
                dirs[:] = sorted(
                    d for d in dirs
                    if not d.startswith(".") and not d.startswith("$")
                )
                for fname in fnames:
                    p = Path(root) / fname
                    if _is_supported(p):
                        files.append(p)
        except PermissionError:
            pass
        files.sort(key=self._file_sort_key, reverse=self._sort_reverse)
        self._entries = [ImageEntry(path=p) for p in files]
        self._current_index = 0 if self._entries else -1

    def load_single_file(self, path: Path) -> None:
        """Load the folder containing *path* and select that file."""
        self.load_folder(path.parent)
        self._current_index = self._index_of(path)

    # ------------------------------------------------------------------ #
    # Navigation                                                           #
    # ------------------------------------------------------------------ #

    @property
    def current_folder(self) -> Optional[Path]:
        return self._folder

    @property
    def current(self) -> Optional[ImageEntry]:
        if 0 <= self._current_index < len(self._entries):
            return self._entries[self._current_index]
        return None

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def count(self) -> int:
        return len(self._entries)

    def go_next(self) -> Optional[ImageEntry]:
        for i in range(self._current_index + 1, len(self._entries)):
            if not self._entries[i].is_dir:
                self._current_index = i
                return self.current
        return self.current

    def go_prev(self) -> Optional[ImageEntry]:
        for i in range(self._current_index - 1, -1, -1):
            if not self._entries[i].is_dir:
                self._current_index = i
                return self.current
        return self.current

    def go_to(self, index: int) -> Optional[ImageEntry]:
        if 0 <= index < len(self._entries):
            self._current_index = index
        return self.current

    def go_to_path(self, path: Path) -> Optional[ImageEntry]:
        idx = self._index_of(path)
        if idx >= 0:
            self._current_index = idx
        return self.current

    def remove_current(self) -> Optional[ImageEntry]:
        """Remove the current entry from the list and return the new current.

        Tries to stay on the next image; if at the end, falls back to the
        previous one.  Returns ``None`` when the list becomes empty.
        """
        idx = self._current_index
        if idx < 0 or idx >= len(self._entries):
            return None
        del self._entries[idx]
        if not self._entries:
            self._current_index = -1
        else:
            self._current_index = min(idx, len(self._entries) - 1)
        return self.current

    def has_next(self) -> bool:
        return any(
            not self._entries[i].is_dir
            for i in range(self._current_index + 1, len(self._entries))
        )

    def has_prev(self) -> bool:
        return any(
            not self._entries[i].is_dir
            for i in range(0, self._current_index)
        )

    # ------------------------------------------------------------------ #
    # Iteration                                                            #
    # ------------------------------------------------------------------ #

    def __iter__(self) -> Iterator[ImageEntry]:
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __getitem__(self, index: int) -> ImageEntry:
        return self._entries[index]

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def sync_folder(self) -> tuple[list[Path], list[Path]]:
        """Re-scan the current folder and update entries in-place.

        Returns ``(added, removed)`` path lists.  Preserves existing
        ``ImageEntry`` objects (thumbnail, search_text, etc.) and keeps the
        current selection pointing at the same file.
        """
        if self._folder is None:
            return [], []
        try:
            children = list(self._folder.iterdir())
        except PermissionError:
            return [], []

        dirs = sorted(
            (
                p for p in children
                if p.is_dir()
                and not p.name.startswith(".")
                and not p.name.startswith("$")
            ),
            key=lambda p: p.name.lower(),
        )
        files = sorted(
            (p for p in children if p.is_file() and _is_supported(p)),
            key=self._file_sort_key,
            reverse=self._sort_reverse,
        )
        new_list = (
            [ImageEntry(path=p, is_dir=True) for p in dirs]
            + [ImageEntry(path=p) for p in files]
        )

        old_path_set = {e.path for e in self._entries}
        new_path_set = {e.path for e in new_list}
        added   = [e.path for e in new_list    if e.path not in old_path_set]
        removed = [e.path for e in self._entries if e.path not in new_path_set]

        if not added and not removed:
            return [], []

        # Carry over thumbnail / metadata / search_text from existing entries
        existing = {e.path: e for e in self._entries}
        merged = [existing.get(e.path, e) for e in new_list]

        current_path = (
            self._entries[self._current_index].path
            if 0 <= self._current_index < len(self._entries)
            else None
        )
        self._entries = merged

        if current_path is not None:
            idx = self._index_of(current_path)
            self._current_index = idx if idx >= 0 else min(self._current_index, len(self._entries) - 1)
        else:
            self._current_index = -1

        return added, removed

    def _index_of(self, path: Path) -> int:
        for i, entry in enumerate(self._entries):
            if entry.path == path:
                return i
        return -1
