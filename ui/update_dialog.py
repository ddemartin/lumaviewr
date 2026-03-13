"""Update-available dialog for Pix42."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

_STYLE = """
QDialog {
    background: #1e1e1e;
}
QLabel {
    color: #ccc;
    background: transparent;
}
QLabel#title {
    color: #fff;
    font-size: 16px;
    font-weight: bold;
}
QLabel#subtitle {
    color: #aaa;
    font-size: 12px;
}
QLabel#versionLabel {
    color: #888;
    font-size: 11px;
}
QLabel#versionNew {
    color: #5a9fd4;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#downloadBtn {
    background: #2a82da;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
    padding: 8px 22px;
}
QPushButton#downloadBtn:hover  { background: #3a92ea; }
QPushButton#downloadBtn:pressed { background: #1a72ca; }
QPushButton#laterBtn {
    background: #333;
    color: #aaa;
    border: 1px solid #444;
    border-radius: 6px;
    font-size: 12px;
    padding: 7px 18px;
}
QPushButton#laterBtn:hover  { background: #444; color: #ccc; }
QPushButton#laterBtn:pressed { background: #555; }
QFrame#divider {
    color: #333;
}
"""


class UpdateDialog(QDialog):
    def __init__(
        self,
        latest_version: str,
        download_url: str,
        current_version: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(380, 220)
        self.setModal(False)
        self.setStyleSheet(_STYLE)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._download_url = download_url
        self._build_ui(latest_version, current_version)

    def _build_ui(self, latest: str, current: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(0)

        title = QLabel("A new version of Pix42 is available!")
        title.setObjectName("title")
        root.addWidget(title)

        root.addSpacing(10)

        subtitle = QLabel("Download the latest version to get new features and fixes.")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addSpacing(16)

        ver_row = QHBoxLayout()
        ver_row.setSpacing(8)

        if current:
            cur_lbl = QLabel(f"Current: {current}")
            cur_lbl.setObjectName("versionLabel")
            arr_lbl = QLabel("→")
            arr_lbl.setObjectName("versionLabel")
            ver_row.addWidget(cur_lbl)
            ver_row.addWidget(arr_lbl)

        new_lbl = QLabel(f"New: {latest}")
        new_lbl.setObjectName("versionNew")
        ver_row.addWidget(new_lbl)
        ver_row.addStretch()
        root.addLayout(ver_row)

        root.addSpacing(20)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(div)

        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        download_btn = QPushButton("Download")
        download_btn.setObjectName("downloadBtn")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.clicked.connect(self._open_download)

        later_btn = QPushButton("Later")
        later_btn.setObjectName("laterBtn")
        later_btn.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(later_btn)
        btn_row.addWidget(download_btn)
        root.addLayout(btn_row)

    def _open_download(self) -> None:
        QDesktopServices.openUrl(QUrl(self._download_url))
        self.accept()
