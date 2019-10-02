from .core.animate import *
from .core.widgets import *
from .models.list_model import ListView, ListModel, ListModelItem
from .structure.left_widget import LeftWidget
from .structure.right_widget import RightWidget


def main():
    app = QApplication([])

    w = main_widget(QWidget())
    w.resize(800, 600)
    main_lay = QVBoxLayout(w)
    main_lay.setContentsMargins(0, 0, 0, 0)

    splitter = LeftRightSplitter(w)
    main_lay.addWidget(splitter)

    left_widget = LeftWidget(splitter)
    right_widget = RightWidget(app, splitter)

    splitter.add_widget(left_widget, LeftRightSplitter.LEFT)
    splitter.add_widget(right_widget, LeftRightSplitter.RIGHT)
    splitter.setSizes([100, 200])

    w.show()

    tray_icon = SystemTrayIcon(favicon(), w, app)
    tray_icon.show()
    # tray_icon.raise_()
    tray_icon.showMessage("BP Chat is started", "Hello!", favicon())

    app.exec_()