"""Non-modal floating panel shown while the resize tool is active."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QSpinBox, QVBoxLayout, QWidget,
)

_BTN_STYLE = """
    QPushButton {
        background: rgba(60,60,60,220);
        color: #ccc;
        border: 1px solid #666;
        border-radius: 4px;
        padding: 4px 14px;
        font-size: 12px;
    }
    QPushButton:hover   { background: rgba(90,90,90,240); color: #fff; }
    QPushButton:pressed { background: rgba(70,120,200,220); }
    QPushButton:checked { background: rgba(60,120,200,200); color: #fff; border-color: #4a8ccf; }
    QPushButton:disabled { color: #555; border-color: #444; }
"""
_LBL = "color: #bbb; font-size: 12px;"
_SPIN_STYLE = """
    QSpinBox {
        background: #2a2a2a; color: #eee;
        border: 1px solid #555; border-radius: 3px;
        padding: 2px 4px; font-size: 12px;
    }
    QSpinBox:focus { border-color: #4a7ab5; }
    QSpinBox::up-button, QSpinBox::down-button { width: 16px; }
"""
_COMBO_STYLE = """
    QComboBox {
        background: #2a2a2a; color: #eee; border: 1px solid #555;
        border-radius: 3px; padding: 2px 6px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #2a2a2a; color: #eee;
        selection-background-color: #3a5a8a;
    }
"""
_EDIT_STYLE = """
    QLineEdit {
        background: #2a2a2a; color: #eee; border: 1px solid #555;
        border-radius: 3px; padding: 2px 6px; font-size: 12px;
    }
    QLineEdit:focus { border-color: #4a7ab5; }
"""


def _lbl(text: str, parent: QWidget) -> QLabel:
    l = QLabel(text, parent)
    l.setStyleSheet(_LBL)
    return l


class ResizeBar(QWidget):
    """Floating panel for image resize (pixels / percent / max-fit)."""

    cancel_requested    = Signal()
    save_as_requested   = Signal()
    overwrite_requested = Signal()

    _MODE_PIXELS  = 0
    _MODE_PERCENT = 1
    _MODE_MAXFIT  = 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._orig_w: int = 0
        self._orig_h: int = 0
        self._updating: bool = False
        self._overwrite_allowed: bool = True

        # --- Mode radios ---
        self._radio_px  = QRadioButton("Pixels",  self)
        self._radio_pct = QRadioButton("Percent", self)
        self._radio_fit = QRadioButton("Max fit", self)
        self._radio_px.setChecked(True)
        self._mode_grp = QButtonGroup(self)
        for i, rb in enumerate((self._radio_px, self._radio_pct, self._radio_fit)):
            self._mode_grp.addButton(rb, i)
            rb.setStyleSheet("color: #ccc; font-size: 12px;")

        self._orig_lbl = QLabel("", self)
        self._orig_lbl.setStyleSheet("color: #666; font-size: 11px;")

        # --- Spinboxes ---
        self._spin_w = QSpinBox(self)
        self._spin_w.setRange(1, 99999)
        self._spin_w.setValue(1920)
        self._spin_w.setFixedWidth(82)
        self._spin_w.setStyleSheet(_SPIN_STYLE)

        self._btn_lock = QPushButton("🔗", self)
        self._btn_lock.setCheckable(True)
        self._btn_lock.setChecked(True)
        self._btn_lock.setFixedSize(28, 28)
        self._btn_lock.setToolTip("Lock aspect ratio")
        self._btn_lock.setStyleSheet(_BTN_STYLE)

        self._spin_h = QSpinBox(self)
        self._spin_h.setRange(1, 99999)
        self._spin_h.setValue(1080)
        self._spin_h.setFixedWidth(82)
        self._spin_h.setStyleSheet(_SPIN_STYLE)

        self._unit_lbl = QLabel("px", self)
        self._unit_lbl.setStyleSheet(_LBL)

        # --- Resample ---
        self._combo_resample = QComboBox(self)
        self._combo_resample.addItems(["Nearest", "Bilinear", "Bicubic", "Lanczos"])
        self._combo_resample.setCurrentText("Lanczos")
        self._combo_resample.setStyleSheet(_COMBO_STYLE)
        self._combo_resample.setFixedWidth(92)

        # --- Batch + suffix ---
        self._chk_batch = QCheckBox("Apply to all in folder", self)
        self._chk_batch.setStyleSheet("color: #bbb; font-size: 12px;")

        self._suffix_edit = QLineEdit("_resized", self)
        self._suffix_edit.setFixedWidth(110)
        self._suffix_edit.setStyleSheet(_EDIT_STYLE)
        self._suffix_edit.setToolTip(
            "Suffix appended to the filename when saving with Save As.\n"
            "Batch mode: all files are saved automatically using this suffix."
        )

        # --- Buttons ---
        self._btn_cancel    = QPushButton("Cancel", self)
        self._btn_save_as   = QPushButton("Save As…", self)
        self._btn_overwrite = QPushButton("Overwrite", self)
        for b in (self._btn_cancel, self._btn_save_as, self._btn_overwrite):
            b.setStyleSheet(_BTN_STYLE)

        # --- Layout ---
        row_mode = QHBoxLayout()
        row_mode.setSpacing(8)
        row_mode.addWidget(_lbl("Mode:", self))
        row_mode.addWidget(self._radio_px)
        row_mode.addWidget(self._radio_pct)
        row_mode.addWidget(self._radio_fit)
        row_mode.addStretch()
        row_mode.addWidget(self._orig_lbl)

        row_dims = QHBoxLayout()
        row_dims.setSpacing(6)
        row_dims.addWidget(_lbl("W:", self))
        row_dims.addWidget(self._spin_w)
        row_dims.addWidget(self._btn_lock)
        row_dims.addWidget(_lbl("H:", self))
        row_dims.addWidget(self._spin_h)
        row_dims.addWidget(self._unit_lbl)
        row_dims.addSpacing(16)
        row_dims.addWidget(_lbl("Resample:", self))
        row_dims.addWidget(self._combo_resample)
        row_dims.addStretch()

        row_opt = QHBoxLayout()
        row_opt.setSpacing(8)
        row_opt.addWidget(self._chk_batch)
        row_opt.addStretch()
        row_opt.addWidget(_lbl("Suffix:", self))
        row_opt.addWidget(self._suffix_edit)

        row_btn = QHBoxLayout()
        row_btn.setSpacing(8)
        row_btn.addStretch()
        row_btn.addWidget(self._btn_cancel)
        row_btn.addWidget(self._btn_save_as)
        row_btn.addWidget(self._btn_overwrite)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)
        lay.addLayout(row_mode)
        lay.addLayout(row_dims)
        lay.addLayout(row_opt)
        lay.addLayout(row_btn)

        # --- Connections ---
        self._mode_grp.idClicked.connect(self._on_mode_changed)
        self._spin_w.valueChanged.connect(self._on_w_changed)
        self._spin_h.valueChanged.connect(self._on_h_changed)
        self._btn_lock.toggled.connect(self._on_lock_toggled)
        self._btn_cancel.clicked.connect(self.cancel_requested)
        self._btn_save_as.clicked.connect(self.save_as_requested)
        self._btn_overwrite.clicked.connect(self.overwrite_requested)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def set_original_size(self, w: int, h: int) -> None:
        self._orig_w = w
        self._orig_h = h
        self._orig_lbl.setText(f"Original: {w} × {h}")
        self._reset_spinboxes()

    def reset(self) -> None:
        self._radio_px.setChecked(True)
        self._btn_lock.setChecked(True)
        self._combo_resample.setCurrentText("Lanczos")
        self._chk_batch.setChecked(False)
        self._suffix_edit.setText("_resized")
        self._unit_lbl.setText("px")
        self._spin_w.blockSignals(True)
        self._spin_h.blockSignals(True)
        self._spin_w.setRange(1, 99999)
        self._spin_h.setRange(1, 99999)
        self._spin_w.blockSignals(False)
        self._spin_h.blockSignals(False)
        self._reset_spinboxes()

    def set_overwrite_allowed(self, allowed: bool) -> None:
        self._overwrite_allowed = allowed
        self._btn_overwrite.setEnabled(allowed)
        self._btn_overwrite.setToolTip(
            "" if allowed else "Overwrite not supported for this format"
        )

    def get_params(self) -> dict:
        """Return a dict with all resize parameters."""
        resample_map = {"Nearest": 0, "Bilinear": 2, "Bicubic": 3, "Lanczos": 1}
        return {
            "mode_id": self._mode_grp.checkedId(),
            "w":        self._spin_w.value(),
            "h":        self._spin_h.value(),
            "resample": resample_map.get(self._combo_resample.currentText(), 1),
            "batch":    self._chk_batch.isChecked(),
            "suffix":   self._suffix_edit.text().strip(),
        }

    @property
    def is_batch(self) -> bool:
        return self._chk_batch.isChecked()

    # ------------------------------------------------------------------ #
    # Paint                                                                #
    # ------------------------------------------------------------------ #

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(22, 22, 22, 228))
        p.setPen(QColor(72, 72, 72))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _reset_spinboxes(self) -> None:
        mode = self._mode_grp.checkedId()
        self._updating = True
        try:
            if mode == self._MODE_PERCENT:
                self._spin_w.setValue(100)
                self._spin_h.setValue(100)
            else:
                self._spin_w.setValue(self._orig_w or 1920)
                self._spin_h.setValue(self._orig_h or 1080)
        finally:
            self._updating = False

    def _aspect_ratio(self) -> float:
        return (self._orig_w / self._orig_h) if self._orig_h else 1.0

    def _on_mode_changed(self, mode_id: int) -> None:
        is_pct = (mode_id == self._MODE_PERCENT)
        self._unit_lbl.setText("%" if is_pct else "px")
        lo, hi = (1, 9900) if is_pct else (1, 99999)
        self._spin_w.blockSignals(True)
        self._spin_h.blockSignals(True)
        self._spin_w.setRange(lo, hi)
        self._spin_h.setRange(lo, hi)
        self._spin_w.blockSignals(False)
        self._spin_h.blockSignals(False)
        self._reset_spinboxes()

    def _on_w_changed(self, v: int) -> None:
        if self._updating or not self._btn_lock.isChecked():
            return
        mode = self._mode_grp.checkedId()
        new_h = v if mode == self._MODE_PERCENT else max(1, round(v / self._aspect_ratio()))
        self._updating = True
        try:
            self._spin_h.setValue(new_h)
        finally:
            self._updating = False

    def _on_h_changed(self, v: int) -> None:
        if self._updating or not self._btn_lock.isChecked():
            return
        mode = self._mode_grp.checkedId()
        new_w = v if mode == self._MODE_PERCENT else max(1, round(v * self._aspect_ratio()))
        self._updating = True
        try:
            self._spin_w.setValue(new_w)
        finally:
            self._updating = False

    def _on_lock_toggled(self, checked: bool) -> None:
        if checked:
            self._on_w_changed(self._spin_w.value())
