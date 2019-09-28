from .core.animate import *
from .core.widgets import *


def main():
    app = QApplication([])

    w = main_widget(QWidget())
    w.resize(800, 600)
    main_lay = QVBoxLayout(w)
    main_lay.setContentsMargins(0, 0, 0, 0)

    splitter = LeftRightSplitter(w)
    main_lay.addWidget(splitter)

    right_widget = QWidget(splitter)
    lay = QVBoxLayout(right_widget)
    lay.setContentsMargins(0, 0, 0, 0)

    left_widget = VLayoutWidget(splitter)
    left_toolbar = Toolbar(left_widget)
    left_widget.addWidget(left_toolbar)

    splitter.add_widget(left_widget, LeftRightSplitter.LEFT)
    splitter.add_widget(right_widget, LeftRightSplitter.RIGHT)
    splitter.setSizes([100, 200])

    toolbar = Toolbar(right_widget)
    lay.addWidget(toolbar)

    button = fix_window(QPushButton("Test", w))
    toolbar.set_widget(button, Toolbar.RIGHT)
    toolbar.set_widget(QLabel('Test'), Toolbar.CENTER)

    settings_button = ImagedButton.by_filename("data/images/settings.png")
    settings_button.clicked.connect(lambda *args: app.exit(0))

    toolbar.set_widget(settings_button, Toolbar.LEFT)

    info_label = InfoLabel(right_widget)
    info_label.setText("Some info...")
    lay.addWidget(info_label)

    lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))
    left_widget.lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

    def _show(*args):
        w.a = fix_window(AnimatedDialog(w))
        w.a.resize(200, 200)
        w.a.exec_()

    button.clicked.connect(_show)

    w.show()

    tray_icon = SystemTrayIcon(favicon(), w, app)
    tray_icon.show()
    # tray_icon.raise_()
    tray_icon.showMessage("BP Chat is started", "Hello!", favicon())

    app.exec_()