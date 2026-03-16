"""Floating bar shown during slideshow mode."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget


class SlideShowBar(QWidget):
    """Floating control bar for slideshow mode."""

    play_pause_requested = Signal()   # toggle play/pause
    stop_requested       = Signal()   # stop and exit slideshow
    order_toggled        = Signal()   # cycle sequential ↔ random
    interval_changed     = Signal(int)  # new interval in seconds

    _STYLE_DARK = """
        QLabel { color: #ccc; font-size: 12px; padding: 0 4px; }
        QPushButton {
            background: rgba(60,60,60,220); color: #ccc;
            border: 1px solid #666; border-radius: 4px;
            padding: 4px 14px; font-size: 12px; min-width: 90px;
        }
        QPushButton:hover   { background: rgba(90,90,90,240); color: #fff; }
        QPushButton:pressed { background: rgba(70,120,200,220); }
        QPushButton#btn_order { min-width: 110px; }
        QPushButton#btn_stop  { min-width: 70px; }
        QSpinBox {
            background: rgba(50,50,50,220); color: #ccc;
            border: 1px solid #666; border-radius: 4px;
            padding: 2px 4px; font-size: 12px; min-width: 56px;
        }
        QSpinBox::up-button, QSpinBox::down-button { width: 18px; }
    """
    _STYLE_LIGHT = """
        QLabel { color: #333; font-size: 12px; padding: 0 4px; }
        QPushButton {
            background: rgba(200,200,200,220); color: #222;
            border: 1px solid #aaa; border-radius: 4px;
            padding: 4px 14px; font-size: 12px; min-width: 90px;
        }
        QPushButton:hover   { background: rgba(180,180,180,240); color: #000; }
        QPushButton:pressed { background: rgba(70,120,200,220); color: #fff; }
        QPushButton#btn_order { min-width: 110px; }
        QPushButton#btn_stop  { min-width: 70px; }
        QSpinBox {
            background: rgba(240,240,240,220); color: #222;
            border: 1px solid #aaa; border-radius: 4px;
            padding: 2px 4px; font-size: 12px; min-width: 56px;
        }
        QSpinBox::up-button, QSpinBox::down-button { width: 18px; }
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._playing = False
        self._random  = False
        self._bg_color = QColor(22, 22, 22, 220)
        self._border_color = QColor(75, 75, 75)

        self._btn_play  = QPushButton("▶  Play", self)
        self._btn_stop  = QPushButton("⏹  Stop", self)
        self._btn_order = QPushButton("🔀 Random", self)
        self._lbl_sep   = QLabel("|", self)
        self._lbl_sec   = QLabel("Interval:", self)
        self._spin      = QSpinBox(self)

        self._btn_stop.setObjectName("btn_stop")
        self._btn_order.setObjectName("btn_order")

        self._spin.setRange(1, 120)
        self._spin.setValue(3)
        self._spin.setSuffix(" s")
        self._spin.setToolTip("Seconds between slides (1–120)")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        lay.addWidget(self._btn_play)
        lay.addWidget(self._btn_stop)
        lay.addWidget(self._lbl_sep)
        lay.addWidget(self._btn_order)
        lay.addWidget(self._lbl_sep)
        lay.addWidget(self._lbl_sec)
        lay.addWidget(self._spin)

        self.setStyleSheet(self._STYLE_DARK)

        self._btn_play.clicked.connect(self._on_play_pause)
        self._btn_stop.clicked.connect(self.stop_requested)
        self._btn_order.clicked.connect(self._on_order)
        self._spin.valueChanged.connect(self.interval_changed)

    # ------------------------------------------------------------------ #

    def _on_play_pause(self) -> None:
        self._playing = not self._playing
        self._update_play_btn()
        self.play_pause_requested.emit()

    def _on_order(self) -> None:
        self._random = not self._random
        self._update_order_btn()
        self.order_toggled.emit()

    def _update_play_btn(self) -> None:
        self._btn_play.setText("⏸  Pause" if self._playing else "▶  Play")

    def _update_order_btn(self) -> None:
        self._btn_order.setText("↕  Sequential" if self._random else "🔀 Random")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        self._update_play_btn()

    def reset(self) -> None:
        """Reset to initial state (paused, sequential)."""
        self._playing = False
        self._random  = False
        self._update_play_btn()
        self._update_order_btn()

    @property
    def is_random(self) -> bool:
        return self._random

    @property
    def interval(self) -> int:
        return self._spin.value()

    # ------------------------------------------------------------------ #

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
