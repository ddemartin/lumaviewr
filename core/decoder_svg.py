"""SVG decoder using Qt's built-in QSvgRenderer — no extra dependencies."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

from .decoder_base import BaseDecoder, ImageMetadata, Region

_SUPPORTED = (".svg", ".svgz")

# Fallback render size when the SVG has no explicit width/height
_DEFAULT_SIZE = 1000


def _render(path: Path, size: QSize) -> QImage:
    """Render the SVG at *size* onto a transparent QImage."""
    renderer = QSvgRenderer(str(path))
    image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter, QRectF(image.rect()))
    painter.end()
    return image


def _native_size(path: Path) -> QSize:
    """Return the SVG's declared size, falling back to a square default."""
    renderer = QSvgRenderer(str(path))
    size = renderer.defaultSize()
    if not size.isValid() or size.width() <= 0 or size.height() <= 0:
        return QSize(_DEFAULT_SIZE, _DEFAULT_SIZE)
    return size


class SvgDecoder(BaseDecoder):
    """Renders SVG/SVGZ files via Qt's built-in QSvgRenderer."""

    SUPPORTED_EXTENSIONS = _SUPPORTED

    def probe(self, path: Path) -> float:
        return 1.0 if path.suffix.lower() in _SUPPORTED else 0.0

    def read_metadata(self, path: Path) -> ImageMetadata:
        try:
            size = _native_size(path)
            return ImageMetadata(
                width=size.width(),
                height=size.height(),
                channels=4,
                bit_depth=8,
                color_space="sRGB",
                format_name="SVG",
            )
        except Exception:
            return ImageMetadata(format_name="SVG")

    def decode_preview(self, path: Path, max_size: int) -> QImage:
        native = _native_size(path)
        w, h = native.width(), native.height()
        scale = min(max_size / max(w, h, 1), 1.0) if max(w, h) > max_size else 1.0
        size = QSize(max(1, int(w * scale)), max(1, int(h * scale)))
        return _render(path, size)

    def decode_full(self, path: Path) -> QImage:
        return _render(path, _native_size(path))

    def decode_region(self, path: Path, region: Region, scale: float) -> QImage:
        native = _native_size(path)
        full = _render(path, native)
        cropped = full.copy(region.x, region.y, region.width, region.height)
        if scale != 1.0:
            cropped = cropped.scaled(
                max(1, int(region.width * scale)),
                max(1, int(region.height * scale)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        return cropped
