"""Floating panel for live image adjustments (brightness, contrast, gamma, saturation)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget,
)

def _slider_style(theme: str) -> str:
    groove = "#ccc" if theme == "light" else "#3a3a3a"
    handle = "#666" if theme == "light" else "#aaa"
    handle_hover = "#333" if theme == "light" else "#fff"
    return f"""
    QSlider::groove:horizontal {{
        height: 4px; background: {groove}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px; height: 12px; margin: -4px 0;
        border-radius: 6px; background: {handle};
    }}
    QSlider::handle:horizontal:hover {{ background: {handle_hover}; }}
    QSlider::sub-page:horizontal {{ background: #4a7ab5; border-radius: 2px; }}
"""


def _btn_style(theme: str) -> str:
    if theme == "light":
        return """
    QPushButton {
        background: rgba(200,200,200,220); color: #222;
        border: 1px solid #aaa; border-radius: 4px;
        padding: 4px 14px; font-size: 12px;
    }
    QPushButton:hover   { background: rgba(180,180,180,240); color: #000; }
    QPushButton:pressed { background: rgba(70,120,200,220); color: #fff; }
    QPushButton:disabled { color: #aaa; border-color: #ccc; }
"""
    return """
    QPushButton {
        background: rgba(60,60,60,220); color: #ccc;
        border: 1px solid #666; border-radius: 4px;
        padding: 4px 14px; font-size: 12px;
    }
    QPushButton:hover   { background: rgba(90,90,90,240); color: #fff; }
    QPushButton:pressed { background: rgba(70,120,200,220); }
    QPushButton:disabled { color: #555; border-color: #444; }
"""


class _SliderRow(QWidget):
    value_changed = Signal(int)

    def __init__(
        self,
        label: str,
        lo: int,
        hi: int,
        default: int,
        fmt_fn=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._default = default
        self._fmt = fmt_fn or (lambda v: f"{v:+d}" if v != 0 else " 0")

        self._name_lbl = QLabel(label, self)
        self._name_lbl.setFixedWidth(82)
        self._name_lbl.setStyleSheet("color: #bbb; font-size: 12px;")

        self._slider = QSlider(Qt.Orientation.Horizontal, self)
        self._slider.setRange(lo, hi)
        self._slider.setValue(default)
        self._slider.setStyleSheet(_slider_style("dark"))

        self._val_lbl = QLabel(self._fmt(default), self)
        self._val_lbl.setFixedWidth(46)
        self._val_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._val_lbl.setStyleSheet("color: #eee; font-size: 12px; font-family: monospace;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        lay.addWidget(self._name_lbl)
        lay.addWidget(self._slider, stretch=1)
        lay.addWidget(self._val_lbl)

        self._slider.valueChanged.connect(self._on_change)

    def _on_change(self, v: int) -> None:
        self._val_lbl.setText(self._fmt(v))
        self.value_changed.emit(v)

    def value(self) -> int:
        return self._slider.value()

    def reset(self) -> None:
        self._slider.setValue(self._default)

    def is_default(self) -> bool:
        return self._slider.value() == self._default

    def apply_theme(self, theme: str) -> None:
        if theme == "light":
            name_color, val_color = "#444", "#111"
        else:
            name_color, val_color = "#bbb", "#eee"
        self._name_lbl.setStyleSheet(f"color: {name_color}; font-size: 12px;")
        self._val_lbl.setStyleSheet(
            f"color: {val_color}; font-size: 12px; font-family: monospace;"
        )
        self._slider.setStyleSheet(_slider_style(theme))


class AdjustBar(QWidget):
    """Floating panel for live brightness/contrast/gamma/saturation adjustments."""

    params_changed      = Signal()
    cancel_requested    = Signal()
    save_as_requested   = Signal()
    overwrite_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._overwrite_allowed = True
        self._bg_color = QColor(22, 22, 22, 228)
        self._border_color = QColor(72, 72, 72)

        self._brightness = _SliderRow("Brightness", -100, 100, 0, parent=self)
        self._contrast   = _SliderRow("Contrast",   -100, 100, 0, parent=self)
        self._gamma      = _SliderRow(
            "Gamma", 10, 300, 100,
            fmt_fn=lambda v: f"{v / 100:.2f}",
            parent=self,
        )
        self._saturation = _SliderRow("Saturation", -100, 100, 0, parent=self)

        self._btn_cancel    = QPushButton("Cancel", self)
        self._btn_reset     = QPushButton("Reset All", self)
        self._btn_save_as   = QPushButton("Save As…", self)
        self._btn_overwrite = QPushButton("Overwrite", self)
        for btn in (self._btn_cancel, self._btn_reset, self._btn_save_as, self._btn_overwrite):
            btn.setStyleSheet(_btn_style("dark"))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_cancel)
        btn_row.addWidget(self._btn_reset)
        btn_row.addWidget(self._btn_save_as)
        btn_row.addWidget(self._btn_overwrite)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)
        lay.addWidget(self._brightness)
        lay.addWidget(self._contrast)
        lay.addWidget(self._gamma)
        lay.addWidget(self._saturation)
        lay.addLayout(btn_row)

        for row in (self._brightness, self._contrast, self._gamma, self._saturation):
            row.value_changed.connect(lambda _: self.params_changed.emit())

        self._btn_cancel.clicked.connect(self.cancel_requested)
        self._btn_reset.clicked.connect(self._reset_all)
        self._btn_save_as.clicked.connect(self.save_as_requested)
        self._btn_overwrite.clicked.connect(self.overwrite_requested)

    def apply_theme(self, theme: str) -> None:
        if theme == "light":
            self._bg_color = QColor(230, 230, 230, 240)
            self._border_color = QColor(180, 180, 180)
        else:
            self._bg_color = QColor(22, 22, 22, 228)
            self._border_color = QColor(72, 72, 72)
        btn_s = _btn_style(theme)
        for btn in (self._btn_cancel, self._btn_reset, self._btn_save_as, self._btn_overwrite):
            btn.setStyleSheet(btn_s)
        for row in (self._brightness, self._contrast, self._gamma, self._saturation):
            row.apply_theme(theme)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), self._bg_color)
        p.setPen(self._border_color)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def get_params(self) -> tuple[int, int, int, int]:
        """Return (brightness, contrast, gamma_slider, saturation)."""
        return (
            self._brightness.value(),
            self._contrast.value(),
            self._gamma.value(),
            self._saturation.value(),
        )

    def is_identity(self) -> bool:
        return all(
            r.is_default()
            for r in (self._brightness, self._contrast, self._gamma, self._saturation)
        )

    def set_overwrite_allowed(self, allowed: bool) -> None:
        self._overwrite_allowed = allowed
        self._btn_overwrite.setEnabled(allowed)
        if not allowed:
            self._btn_overwrite.setToolTip("Overwrite not supported for this format")
        else:
            self._btn_overwrite.setToolTip("")

    def _reset_all(self) -> None:
        for row in (self._brightness, self._contrast, self._gamma, self._saturation):
            row.reset()
