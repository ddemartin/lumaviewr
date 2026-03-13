"""Background update checker — polls https://www.demahub.com/pix42/version.json once a week."""
from __future__ import annotations

import json
import logging
from datetime import date

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

log = logging.getLogger(__name__)

VERSION_URL = "https://www.demahub.com/pix42/version.json"
CHECK_INTERVAL_DAYS = 7


class UpdateChecker(QObject):
    """Fetches version.json from the server and emits update_available if a newer version exists."""

    update_available = Signal(str, str)  # (latest_version, download_url)
    up_to_date = Signal()               # emitted on manual check when already on latest
    check_error = Signal(str)           # emitted on manual check when network fails

    def __init__(self, current_version: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current = current_version
        self._manual = False
        self._nam = QNetworkAccessManager(self)

    def check_if_due(self) -> None:
        """Check for updates only if CHECK_INTERVAL_DAYS have passed since the last check."""
        from utils.settings_manager import SettingsManager
        last = SettingsManager().last_update_check
        if last:
            try:
                delta = (date.today() - date.fromisoformat(last)).days
                if delta < CHECK_INTERVAL_DAYS:
                    log.debug("Update check skipped (last: %s)", last)
                    return
            except ValueError:
                pass
        self._fetch(manual=False)

    def check_now(self) -> None:
        """Force an immediate update check (manual — always gives feedback)."""
        self._fetch(manual=True)

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _fetch(self, manual: bool = False) -> None:
        self._manual = manual
        req = QNetworkRequest(QUrl(VERSION_URL))
        req.setTransferTimeout(10_000)
        reply = self._nam.get(req)
        reply.finished.connect(lambda: self._on_reply(reply))

    def _on_reply(self, reply: QNetworkReply) -> None:
        from utils.settings_manager import SettingsManager
        SettingsManager().last_update_check = date.today().isoformat()
        manual = self._manual
        self._manual = False

        if reply.error() != QNetworkReply.NetworkError.NoError:
            log.warning("Update check failed: %s", reply.errorString())
            if manual:
                self.check_error.emit(reply.errorString())
            reply.deleteLater()
            return

        try:
            data = json.loads(bytes(reply.readAll()))
            latest = data.get("version", "")
            download_url = data.get("download_url", "https://www.demahub.com/pix42/download")
            if latest and self._is_newer(latest):
                self.update_available.emit(latest, download_url)
            elif manual:
                self.up_to_date.emit()
        except Exception as exc:
            log.warning("Update check parse error: %s", exc)
            if manual:
                self.check_error.emit(str(exc))
        finally:
            reply.deleteLater()

    def _is_newer(self, remote: str) -> bool:
        def _parse(v: str) -> tuple:
            try:
                return tuple(int(x) for x in v.strip().split("."))
            except ValueError:
                return (0,)
        return _parse(remote) > _parse(self._current)
