from PyQt5.QtWidgets import QWidget, QVBoxLayout


class VLayoutWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, widget):
        self.lay.addWidget(widget)
