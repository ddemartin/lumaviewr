"""System tray icon for Luma Viewer daemon mode."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    """
    Minimal system tray icon.

    Signals
    -------
    show_window_requested
        Emitted when the user wants to bring the main window to the front
        (double-click on the tray icon, or "Open Luma" menu action).
    quit_requested
        Emitted when the user chooses "Quit" from the tray menu.
    """

    show_window_requested = Signal()
    quit_requested = Signal()

    def __init__(self, icon: QIcon, parent=None) -> None:
        super().__init__(icon, parent)

        menu = QMenu()
        open_action = menu.addAction("Open Luma")
        open_action.triggered.connect(self.show_window_requested)
        menu.addSeparator()
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested)

        self.setContextMenu(menu)
        self.setToolTip("Luma Viewer")
        self.activated.connect(self._on_activated)

    # ------------------------------------------------------------------ #

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
