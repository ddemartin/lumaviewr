"""Application bootstrap: creates QApplication and wires global services."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QApplication

from config import config, AppConfig, ASSETS_DIR
from utils.logging import setup_logging

if TYPE_CHECKING:
    from utils.single_instance import SingleInstance

log = logging.getLogger(__name__)


class Pix42App:
    """
    Thin wrapper around QApplication.

    Responsible for:
    - setting up logging
    - creating QApplication with correct attributes
    - applying global stylesheet
    - wiring single-instance IPC
    - managing the system tray icon
    - launching the main window
    """

    def __init__(
        self,
        argv: list[str],
        app_config: Optional[AppConfig] = None,
        single_instance: "Optional[SingleInstance]" = None,
        start_in_tray: bool = False,
    ) -> None:
        self._cfg = app_config or config
        self._cfg.ensure_dirs()

        setup_logging(
            level=getattr(logging, self._cfg.log_level, logging.INFO),
            log_file=self._cfg.data_dir / "viewer.log",
        )
        log.info("Starting Pix42")

        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        self._qapp = QApplication.instance() or QApplication(argv)
        self._qapp.setApplicationName("Pix42")
        self._qapp.setOrganizationName("Pix42")
        self._qapp.setStyle("Fusion")

        from utils.settings_manager import SettingsManager as _SM
        _saved_theme = _SM().theme
        self.apply_theme(_saved_theme)  # palette + stylesheet (no window yet)
        self._apply_app_icon()

        self._start_in_tray = start_in_tray

        # Prevent Qt from quitting the event loop when the last window is
        # hidden (needed for tray-only mode).
        self._qapp.setQuitOnLastWindowClosed(False)

        QThreadPool.globalInstance().setMaxThreadCount(
            self._cfg.loader.thread_pool_size
        )

        from ui.main_window import MainWindow
        self._window = MainWindow()
        self._window._app = self  # back-reference so Settings dialog can reach Pix42App
        # Apply theme to window widgets (GridView, MetadataPanel, etc.) now that they exist
        self._window.apply_theme(_saved_theme)

        # ------------------------------------------------------------------ #
        # System tray                                                          #
        # ------------------------------------------------------------------ #
        self._tray = None
        self._setup_tray()

        # ------------------------------------------------------------------ #
        # Single-instance IPC                                                 #
        # ------------------------------------------------------------------ #
        self._si = single_instance
        if single_instance is not None:
            single_instance.file_open_requested.connect(self._on_ipc_open)

        self._start_in_tray = start_in_tray

    # ------------------------------------------------------------------ #
    # Public                                                               #
    # ------------------------------------------------------------------ #

    def run(self, open_path: Optional[Path] = None) -> int:
        """Show the window (or stay hidden in tray) and enter the event loop."""
        if self._start_in_tray:
            # Stay hidden; tray icon is already shown in _setup_tray()
            pass
        else:
            self._window.show()

        if open_path and open_path.exists():
            self._window.open_path(open_path)
            if self._start_in_tray:
                self._show_window()

        ret = self._qapp.exec()
        # Give active workers (e.g. in-flight ffmpeg subprocesses) up to 3 s
        # to finish, then return anyway so the Python process can exit cleanly.
        QThreadPool.globalInstance().waitForDone(3000)
        return ret

    # ------------------------------------------------------------------ #
    # Tray                                                                 #
    # ------------------------------------------------------------------ #

    def _setup_tray(self) -> None:
        """Create and show the tray icon if the setting is enabled or --tray was passed."""
        from utils.settings_manager import SettingsManager
        settings = SettingsManager()

        if settings.close_to_tray or self._start_in_tray:
            self._create_tray()

    def _create_tray(self) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            log.warning("System tray not available on this desktop")
            return

        from PySide6.QtGui import QIcon
        from ui.tray_icon import TrayIcon

        icon_path = ASSETS_DIR / "app" / "icon.svg"
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
        self._tray = TrayIcon(icon, self._qapp)
        self._tray.show_window_requested.connect(self._show_window)
        self._tray.quit_requested.connect(self._quit)
        self._tray.show()

        # Tell the window a tray is available so closeEvent can hide instead
        # of quitting.
        self._window.set_tray_available(True)

    def ensure_tray(self) -> None:
        """Create the tray icon if it hasn't been created yet (called from Settings)."""
        if self._tray is None:
            self._create_tray()
        elif not self._tray.isVisible():
            self._tray.show()
            self._window.set_tray_available(True)

    def hide_tray(self) -> None:
        """Hide and destroy the tray icon (called from Settings when disabled)."""
        if self._tray is not None:
            self._tray.hide()
            self._window.set_tray_available(False)

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _quit(self) -> None:
        self._window._settings.save_geometry(self._window.saveGeometry())
        QApplication.quit()

    # ------------------------------------------------------------------ #
    # IPC                                                                  #
    # ------------------------------------------------------------------ #

    def _on_ipc_open(self, path_str: str) -> None:
        path = Path(path_str)
        if path.exists():
            self._window.open_path(path)
        self._show_window()

    # ------------------------------------------------------------------ #
    # Theme                                                                #
    # ------------------------------------------------------------------ #

    def apply_theme(self, theme: str) -> None:
        """Apply 'dark' or 'light' theme to the entire application."""
        if theme == "light":
            self._apply_light_palette()
            self._apply_light_stylesheet()
        else:
            self._apply_dark_palette()
            self._apply_dark_stylesheet()
        if hasattr(self, "_window"):
            self._window.apply_theme(theme)

    def _apply_app_icon(self) -> None:
        from PySide6.QtGui import QIcon
        icon_path = ASSETS_DIR / "app" / "icon.svg"
        if icon_path.exists():
            self._qapp.setWindowIcon(QIcon(str(icon_path)))

    def _apply_dark_palette(self) -> None:
        from PySide6.QtGui import QPalette, QColor
        palette = QPalette()
        dark   = QColor(30,  30,  30)
        mid    = QColor(53,  53,  53)
        text   = QColor(220, 220, 220)
        bright = QColor(42, 130, 218)
        link   = QColor(100, 160, 230)

        palette.setColor(QPalette.ColorRole.Window,          dark)
        palette.setColor(QPalette.ColorRole.WindowText,      text)
        palette.setColor(QPalette.ColorRole.Base,            QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.AlternateBase,   mid)
        palette.setColor(QPalette.ColorRole.ToolTipBase,     mid)
        palette.setColor(QPalette.ColorRole.ToolTipText,     text)
        palette.setColor(QPalette.ColorRole.Text,            text)
        palette.setColor(QPalette.ColorRole.Button,          mid)
        palette.setColor(QPalette.ColorRole.ButtonText,      text)
        palette.setColor(QPalette.ColorRole.BrightText,      QColor(255, 100, 100))
        palette.setColor(QPalette.ColorRole.Link,            link)
        palette.setColor(QPalette.ColorRole.Highlight,       bright)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self._qapp.setPalette(palette)

    def _apply_light_palette(self) -> None:
        from PySide6.QtGui import QPalette, QColor
        palette = QPalette()
        window  = QColor(240, 240, 240)
        base    = QColor(255, 255, 255)
        altbase = QColor(245, 245, 245)
        text    = QColor(30,  30,  30)
        mid     = QColor(210, 210, 210)
        tooltip_bg = QColor(255, 255, 220)
        bright  = QColor(42, 130, 218)
        link    = QColor(0, 100, 200)

        palette.setColor(QPalette.ColorRole.Window,          window)
        palette.setColor(QPalette.ColorRole.WindowText,      text)
        palette.setColor(QPalette.ColorRole.Base,            base)
        palette.setColor(QPalette.ColorRole.AlternateBase,   altbase)
        palette.setColor(QPalette.ColorRole.ToolTipBase,     tooltip_bg)
        palette.setColor(QPalette.ColorRole.ToolTipText,     text)
        palette.setColor(QPalette.ColorRole.Text,            text)
        palette.setColor(QPalette.ColorRole.Button,          mid)
        palette.setColor(QPalette.ColorRole.ButtonText,      text)
        palette.setColor(QPalette.ColorRole.BrightText,      QColor(200, 0, 0))
        palette.setColor(QPalette.ColorRole.Link,            link)
        palette.setColor(QPalette.ColorRole.Highlight,       bright)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self._qapp.setPalette(palette)

    def _apply_dark_stylesheet(self) -> None:
        self._qapp.setStyleSheet("""
            QToolTip {
                color: #e8e8e8;
                background-color: #3c3c3c;
                border: 1px solid #666;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QSplitter::handle {
                background: #444;
            }
            QSplitter::handle:hover {
                background: #2a82da;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6a6a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #252525;
                height: 10px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: #505050;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6a6a6a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QMenuBar {
                background: #2a2a2a;
                color: #d8d8d8;
                border-bottom: 1px solid #444;
            }
            QMenuBar::item:selected {
                background: #3a3a3a;
            }
            QMenu {
                background: #2e2e2e;
                color: #d8d8d8;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background: #2a82da;
                color: #fff;
            }
            QToolBar {
                background: #242424;
                border-bottom: 1px solid #3a3a3a;
                spacing: 1px;
                padding: 2px 4px;
            }
            QToolBar::separator {
                background: #444;
                width: 1px;
                margin: 4px 3px;
            }
            QToolBar QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                color: #d8d8d8;
            }
            QToolBar QToolButton:hover {
                background: rgba(255, 255, 255, 0.10);
            }
            QToolBar QToolButton:pressed {
                background: rgba(255, 255, 255, 0.18);
            }
            QToolBar QToolButton:checked {
                background: rgba(42, 130, 218, 0.35);
            }
            QToolBar QToolButton:disabled {
                opacity: 0.35;
            }
            QToolBar QToolButton[popupMode="2"] {
                padding-right: 6px;
            }
            QStatusBar {
                background: #272727;
                color: #b0b0b0;
                border-top: 1px solid #3a3a3a;
            }
        """)

    def _apply_light_stylesheet(self) -> None:
        self._qapp.setStyleSheet("""
            QToolTip {
                color: #1a1a1a;
                background-color: #ffffc8;
                border: 1px solid #aaa;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QSplitter::handle {
                background: #ccc;
            }
            QSplitter::handle:hover {
                background: #2a82da;
            }
            QScrollBar:vertical {
                background: #e8e8e8;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #b0b0b0;
                border-radius: 4px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #e8e8e8;
                height: 10px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: #b0b0b0;
                border-radius: 4px;
                min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #888;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QMenuBar {
                background: #f0f0f0;
                color: #1a1a1a;
                border-bottom: 1px solid #ccc;
            }
            QMenuBar::item:selected {
                background: #ddd;
            }
            QMenu {
                background: #f8f8f8;
                color: #1a1a1a;
                border: 1px solid #bbb;
            }
            QMenu::item:selected {
                background: #2a82da;
                color: #fff;
            }
            QToolBar {
                background: #383838;
                border-bottom: 1px solid #2a2a2a;
                spacing: 1px;
                padding: 2px 4px;
            }
            QToolBar::separator {
                background: #555;
                width: 1px;
                margin: 4px 3px;
            }
            QToolBar QToolButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
                color: #e8e8e8;
            }
            QToolBar QToolButton:hover {
                background: rgba(255, 255, 255, 0.14);
            }
            QToolBar QToolButton:pressed {
                background: rgba(255, 255, 255, 0.22);
            }
            QToolBar QToolButton:checked {
                background: rgba(42, 130, 218, 0.45);
            }
            QToolBar QToolButton:disabled {
                opacity: 0.35;
            }
            QToolBar QToolButton[popupMode="2"] {
                padding-right: 6px;
            }
            QStatusBar {
                background: #e8e8e8;
                color: #444;
                border-top: 1px solid #ccc;
            }
        """)
