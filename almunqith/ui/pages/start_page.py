"""Home screen: choose a service — recover files, or securely wipe a disk."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton)

from almunqith.ui.i18n import tr


class StartPage(QWidget):
    recover_requested = Signal()
    wipe_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        self._title = QLabel()
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setStyleSheet("font-size: 22px; font-weight: bold;")
        self._hint = QLabel()
        self._hint.setObjectName("subtitle")
        self._hint.setAlignment(Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addSpacing(24)

        cards = QHBoxLayout()
        cards.setSpacing(18)
        self._recover_btn = self._make_card("recover")
        self._wipe_btn = self._make_card("wipe")
        self._recover_btn.clicked.connect(self.recover_requested)
        self._wipe_btn.clicked.connect(self.wipe_requested)
        cards.addStretch(1)
        cards.addWidget(self._recover_btn)
        cards.addWidget(self._wipe_btn)
        cards.addStretch(1)
        layout.addLayout(cards)
        layout.addStretch(2)
        self.retranslate()

    def _make_card(self, kind):
        btn = QPushButton()
        btn.setObjectName("servicecard")
        btn.setMinimumSize(300, 170)
        btn.setCursor(Qt.PointingHandCursor)
        btn._kind = kind
        return btn

    def retranslate(self):
        self._title.setText(tr("home_title"))
        self._hint.setText(tr("home_hint"))
        self._recover_btn.setText(
            f"{tr('svc_recover')}\n\n{tr('svc_recover_desc')}")
        self._wipe_btn.setText(f"{tr('svc_wipe')}\n\n{tr('svc_wipe_desc')}")

    def enter(self):
        pass
