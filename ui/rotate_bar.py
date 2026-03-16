"""Non-modal floating bar shown while the rotate tool is active."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class RotateBar(QWidget):
    """Floating toolbar for rotate mode."""

    rotate_ccw_requested = Signal()
    rotate_cw_requested  = Signal()
    cancel_requested     = Signal()
    save_as_requested    = Signal()
    overwrite_requested  = Signal()

    _STYLE_DARK = """
        QLabel { color: #ccc; font-size: 12px; padding: 0 4px; }
        QPushButton {
            background: rgba(60,60,60,220); color: #ccc;
            border: 1px solid #666; border-radius: 4px;
            padding: 4px 14px; font-size: 12px;
        }
        QPushButton:hover   { background: rgba(90,90,90,240); color: #fff; }
        QPushButton:pressed { background: rgba(70,120,200,220); }
        QPushButton:disabled { color: #555; border-color: #444; }
    """
    _STYLE_LIGHT = """
        QLabel { color: #333; font-size: 12px; padding: 0 4px; }
        QPushButton {
            background: rgba(200,200,200,220); color: #222;
            border: 1px solid #aaa; border-radius: 4px;
            padding: 4px 14px; font-size: 12px;
        }
        QPushButton:hover   { background: rgba(180,180,180,240); color: #000; }
        QPushButton:pressed { background: rgba(70,120,200,220); color: #fff; }
        QPushButton:disabled { color: #aaa; border-color: #ccc; }
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._overwrite_allowed = True
        self._bg_color = QColor(22, 22, 22, 220)
        self._border_color = QColor(75, 75, 75)

        self._btn_ccw       = QPushButton("↺ CCW", self)
        self._lbl_angle     = QLabel("0°", self)
        self._btn_cw        = QPushButton("↻ CW", self)
        self._btn_cancel    = QPushButton("Cancel", self)
        self._btn_save_as   = QPushButton("Save As…", self)
        self._btn_overwrite = QPushButton("Overwrite", self)

        self._lbl_angle.setMinimumWidth(40)
        self._lbl_angle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._btn_save_as.setEnabled(False)
        self._btn_overwrite.setEnabled(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        lay.addWidget(self._btn_ccw)
        lay.addWidget(self._lbl_angle)
        lay.addWidget(self._btn_cw)
        lay.addStretch()
        lay.addWidget(self._btn_cancel)
        lay.addWidget(self._btn_save_as)
        lay.addWidget(self._btn_overwrite)

        self.setStyleSheet(self._STYLE_DARK)

        self._btn_ccw.clicked.connect(self.rotate_ccw_requested)
        self._btn_cw.clicked.connect(self.rotate_cw_requested)
        self._btn_cancel.clicked.connect(self.cancel_requested)
        self._btn_save_as.clicked.connect(self.save_as_requested)
        self._btn_overwrite.clicked.connect(self.overwrite_requested)

    def apply_theme(self, theme: str) -> None:
        if theme == "light":
            self._bg_color = QColor(230, 230, 230, 240)
            self._border_color = QColor(180, 180, 180)
            self.setStyleSheet(self._STYLE_LIGHT)
        else:
            self._bg_color = QColor(22, 22, 22, 220)
            self._border_color = QColor(75, 75, 75)
            self.setStyleSheet(self._STYLE_DARK)
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), self._bg_color)
        p.setPen(self._border_color)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def update_angle(self, degrees: int) -> None:
        self._lbl_angle.setText(f"{degrees}°")
        has_rotation = degrees != 0
        self._btn_save_as.setEnabled(has_rotation)
        self._btn_overwrite.setEnabled(has_rotation and self._overwrite_allowed)

    def set_overwrite_allowed(self, allowed: bool) -> None:
        self._overwrite_allowed = allowed
        if not allowed:
            self._btn_overwrite.setEnabled(False)
            self._btn_overwrite.setToolTip("Overwrite not supported for this format")
        else:
            self._btn_overwrite.setToolTip("")
