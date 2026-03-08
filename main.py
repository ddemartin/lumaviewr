"""Entry point — run with: python -m Luma  OR  python main.py [image_path]"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure package root is importable when run as a plain script
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    argv = sys.argv[:]
    open_path: Path | None = None
    start_in_tray = "--tray" in argv

    # Extract optional image path (first positional argument)
    filtered = []
    for arg in argv[1:]:
        if arg.startswith("-"):
            filtered.append(arg)
        elif open_path is None:
            candidate = Path(arg)
            if candidate.exists():
                open_path = candidate
            else:
                filtered.append(arg)
        else:
            filtered.append(arg)
    argv = [argv[0]] + filtered

    # ------------------------------------------------------------------ #
    # Single-instance check                                                #
    # QLocalSocket needs a QApplication; create it here so app.py can     #
    # reuse the same instance via QApplication.instance().                 #
    # ------------------------------------------------------------------ #
    from PySide6.QtWidgets import QApplication
    _pre = QApplication.instance() or QApplication(sys.argv)

    from utils.single_instance import SingleInstance
    si = SingleInstance()
    if not si.try_become_primary():
        # Another instance is already running — hand off the path and exit.
        if open_path:
            si.send_to_primary(str(open_path))
        return 0

    # This is the primary instance — hand off to the full app.
    from app import LumaApp
    app = LumaApp(argv, single_instance=si, start_in_tray=start_in_tray)
    return app.run(open_path)


if __name__ == "__main__":
    sys.exit(main())
