"""Step 2: choose which file categories to recover."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                               QPushButton)

from almunqith.ui.i18n import tr

# category key -> (label key, enabled) — all categories now have validators
_CATS = [
    ("all", "cat_all", True),
    ("photos", "cat_photos", True),
    ("videos", "cat_videos", True),
    ("documents", "cat_documents", True),
    ("audio", "cat_audio", True),
    ("archives", "cat_archives", True),
]


class TypesPage(QWidget):
    selection_changed = Signal()

    def __init__(self):
        super().__init__()
        self._buttons: dict[str, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 18, 26, 10)
        self._title = QLabel()
        self._title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addSpacing(10)
        grid = QGridLayout()
        grid.setSpacing(12)
        for idx, (key, label_key, enabled) in enumerate(_CATS):
            btn = QPushButton()
            btn.setObjectName("typebtn")
            btn.setCheckable(True)
            btn.setEnabled(enabled)
            if not enabled:
                btn.setToolTip(tr("coming_soon"))
            btn.clicked.connect(lambda _=False, k=key: self._on_click(k))
            self._buttons[key] = btn
            grid.addWidget(btn, idx // 3, idx % 3)
        layout.addLayout(grid)
        layout.addStretch(1)
        self._buttons["all"].setChecked(True)
        self.retranslate()

    def retranslate(self):
        self._title.setText(tr("types_question"))
        self._hint.setText(tr("types_hint"))
        for key, label_key, _ in _CATS:
            self._buttons[key].setText(tr(label_key))

    def _on_click(self, key):
        if key == "all" and self._buttons["all"].isChecked():
            for k, b in self._buttons.items():
                if k != "all":
                    b.setChecked(False)
        elif key != "all" and self._buttons[key].isChecked():
            self._buttons["all"].setChecked(False)
        if not any(b.isChecked() for b in self._buttons.values()):
            self._buttons["all"].setChecked(True)
        self.selection_changed.emit()

    def categories(self) -> set:
        if self._buttons["all"].isChecked():
            return {"all"}
        return {k for k, b in self._buttons.items() if b.isChecked()}

    def enter(self):
        pass

    def can_advance(self) -> bool:
        return bool(self.categories())
