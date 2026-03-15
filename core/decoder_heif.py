"""HEIC/HEIF decoder via pillow-heif + Pillow.

Requires:
    pip install pillow-heif

pillow-heif registers itself as a Pillow plugin, so after registration
Image.open() handles .heic/.heif/.hif transparently — no separate decode
path needed.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage

from .decoder_base import BaseDecoder, ImageMetadata, Region
from .decoder_pillow import _normalize_mode, _pil_to_qimage

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _HEIF_OK = True
except ImportError:
    _HEIF_OK = False

_SUPPORTED = (".heic", ".heif", ".hif", ".avci", ".avcs")


class HeifDecoder(BaseDecoder):
    """Reads HEIC/HEIF files via pillow-heif."""

    SUPPORTED_EXTENSIONS = _SUPPORTED

    def probe(self, path: Path) -> float:
        if not _HEIF_OK:
            return 0.0
        return 1.0 if path.suffix.lower() in _SUPPORTED else 0.0

    def read_metadata(self, path: Path) -> ImageMetadata:
        if not _HEIF_OK:
            return ImageMetadata(format_name="HEIF")
        from PIL import Image, ExifTags, ImageOps
        with Image.open(path) as img:
            exif_raw = {}
            try:
                raw = img._getexif()  # type: ignore[attr-defined]
                if raw:
                    exif_raw = {ExifTags.TAGS.get(k, k): v for k, v in raw.items()}
            except Exception:
                pass
            try:
                transposed = ImageOps.exif_transpose(img)
                w, h = transposed.width, transposed.height
            except Exception:
                w, h = img.width, img.height
            return ImageMetadata(
                width=w,
                height=h,
                channels=len(img.getbands()),
                bit_depth=8,
                color_space="sRGB",
                format_name="HEIF",
                exif=exif_raw,
            )

    def decode_preview(self, path: Path, max_size: int) -> QImage:
        if not _HEIF_OK:
            return QImage()
        from PIL import Image, ImageOps
        with Image.open(path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img = _normalize_mode(img)
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            return _pil_to_qimage(img)

    def decode_region(self, path: Path, region: Region, scale: float) -> QImage:
        if not _HEIF_OK:
            return QImage()
        from PIL import Image, ImageOps
        with Image.open(path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass
            img = _normalize_mode(img)
            box = (region.x, region.y, region.x + region.width, region.y + region.height)
            cropped = img.crop(box)
            if scale != 1.0:
                new_w = max(1, int(cropped.width * scale))
                new_h = max(1, int(cropped.height * scale))
                cropped = cropped.resize((new_w, new_h), Image.LANCZOS)
            return _pil_to_qimage(cropped)

    def can_decode_region(self) -> bool:
        return True
