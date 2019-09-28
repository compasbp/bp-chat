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

    left_toolbar.add_button("settings", Toolbar.LEFT, "settings")
    left_toolbar.add_label("title", Toolbar.CENTER, "BP Chat")
    left_toolbar.add_button("search", Toolbar.RIGHT, "search").clicked.connect(
        lambda *args: left_toolbar.set_page("search"))

    left_toolbar.add_page("search")
    left_toolbar.add_button("back", Toolbar.LEFT, "arrow_back", page='search').clicked.connect(
        lambda *args: left_toolbar.set_page("first"))
    left_toolbar.add_input("input", Toolbar.CENTER, page='search')

    splitter.add_widget(left_widget, LeftRightSplitter.LEFT)
    splitter.add_widget(right_widget, LeftRightSplitter.RIGHT)
    splitter.setSizes([100, 200])

    toolbar = Toolbar(right_widget)
    lay.addWidget(toolbar)

    def _show(*args):
        w.a = fix_window(AnimatedDialog(w))
        w.a.resize(200, 200)
        w.a.exec_()

    toolbar.add_button("group", Toolbar.LEFT, "group").clicked.connect(
        lambda *args: app.exit(0))
    toolbar.add_label("title", Toolbar.CENTER, 'Title')
    toolbar.add_button("menu", Toolbar.RIGHT, "menu").clicked.connect(_show)

    info_label = InfoLabel(right_widget)
    info_label.setText("Some info...")
    lay.addWidget(info_label)

    lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))
    left_widget.lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

    w.show()

    tray_icon = SystemTrayIcon(favicon(), w, app)
    tray_icon.show()
    # tray_icon.raise_()
    tray_icon.showMessage("BP Chat is started", "Hello!", favicon())

    app.exec_()