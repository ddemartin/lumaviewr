"""Application settings dialog."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QDialog, QFrame, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from utils.settings_manager import SettingsManager

_STYLE = """
QDialog {
    background: #1e1e1e;
}
QTabWidget::pane {
    border: 1px solid #333;
    background: #252525;
}
QTabBar::tab {
    background: #2a2a2a;
    color: #aaa;
    padding: 6px 18px;
    border: 1px solid #333;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
}
QTabBar::tab:selected {
    background: #252525;
    color: #fff;
}
QTabBar::tab:hover:!selected {
    background: #333;
    color: #ccc;
}
QLabel {
    color: #ccc;
    background: transparent;
}
QLabel#sectionHeader {
    color: #aaa;
    font-size: 11px;
    font-weight: bold;
    border-bottom: 1px solid #333;
    padding-bottom: 2px;
}
QCheckBox {
    color: #ccc;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background: #2a2a2a;
}
QCheckBox::indicator:checked {
    background: #3a7bd5;
    border-color: #3a7bd5;
}
QCheckBox::indicator:hover {
    border-color: #888;
}
QPushButton#okBtn {
    background: #3a7bd5;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    padding: 6px 22px;
}
QPushButton#okBtn:hover  { background: #4a8be5; }
QPushButton#okBtn:pressed { background: #2a6bc5; }
QPushButton#cancelBtn {
    background: #333;
    color: #ccc;
    border: 1px solid #444;
    border-radius: 6px;
    font-size: 12px;
    padding: 6px 18px;
}
QPushButton#cancelBtn:hover  { background: #444; color: #fff; }
QPushButton#cancelBtn:pressed { background: #555; }
QFrame#divider { color: #333; }
"""


def _swatch_style(color: QColor) -> str:
    return (
        f"background: {color.name()};"
        "border: 1px solid #555;"
        "border-radius: 4px;"
    )


class SettingsDialog(QDialog):
    """
    Modal settings dialog.

    Changes to backdrop color are applied live to *viewer* for instant
    preview.  If the user cancels, the original color is restored.
    """

    def __init__(self, settings: SettingsManager, viewer, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._viewer = viewer

        # Snapshot originals so Cancel can revert
        self._orig_backdrop = QColor(settings.backdrop_color)
        self._orig_confirm_delete = settings.confirm_delete
        self._orig_start_fullscreen = settings.start_fullscreen

        self._current_backdrop = QColor(settings.backdrop_color)

        self.setWindowTitle("Settings")
        self.setFixedSize(420, 340)
        self.setModal(True)
        self.setStyleSheet(_STYLE)
        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI                                                                   #
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        tabs = QTabWidget()
        tabs.addTab(self._appearance_tab(), "Appearance")
        tabs.addTab(self._behavior_tab(), "Behavior")
        root.addWidget(tabs)

        root.addStretch()

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(div)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self._on_cancel)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("okBtn")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    def _appearance_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(12)

        hdr = QLabel("Backdrop")
        hdr.setObjectName("sectionHeader")
        layout.addWidget(hdr)

        row = QHBoxLayout()
        row.setSpacing(10)
        lbl = QLabel("Viewer background color:")
        row.addWidget(lbl)
        row.addStretch()

        self._color_swatch = QPushButton()
        self._color_swatch.setFixedSize(64, 24)
        self._color_swatch.setStyleSheet(_swatch_style(self._current_backdrop))
        self._color_swatch.setToolTip("Click to choose color")
        self._color_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_swatch.clicked.connect(self._pick_color)
        row.addWidget(self._color_swatch)
        layout.addLayout(row)

        layout.addStretch()
        return tab

    def _behavior_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(12)

        hdr = QLabel("File operations")
        hdr.setObjectName("sectionHeader")
        layout.addWidget(hdr)

        self._confirm_delete_cb = QCheckBox("Ask for confirmation before deleting files")
        self._confirm_delete_cb.setChecked(self._orig_confirm_delete)
        layout.addWidget(self._confirm_delete_cb)

        layout.addSpacing(8)

        hdr2 = QLabel("Startup")
        hdr2.setObjectName("sectionHeader")
        layout.addWidget(hdr2)

        self._start_fullscreen_cb = QCheckBox("Start in fullscreen mode")
        self._start_fullscreen_cb.setChecked(self._orig_start_fullscreen)
        layout.addWidget(self._start_fullscreen_cb)

        layout.addStretch()
        return tab

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(
            self._current_backdrop, self, "Choose backdrop color",
        )
        if not color.isValid():
            return
        self._current_backdrop = color
        self._color_swatch.setStyleSheet(_swatch_style(color))
        # Live preview
        self._viewer.set_backdrop_color(color)

    def _on_ok(self) -> None:
        self._settings.backdrop_color = self._current_backdrop.name()
        self._settings.confirm_delete = self._confirm_delete_cb.isChecked()
        self._settings.start_fullscreen = self._start_fullscreen_cb.isChecked()
        self.accept()

    def _on_cancel(self) -> None:
        # Revert live backdrop preview
        self._viewer.set_backdrop_color(self._orig_backdrop)
        self.reject()
