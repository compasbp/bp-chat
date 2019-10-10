from ..core.animate import *
from ..core.widgets import *
from ..models.list_model import ListView, ChatsModel


class LeftWidget(VLayoutWidget):

    MARGINS = (0, 0, 1, 0)

    def __init__(self, splitter):
        super().__init__(splitter)

        toolbar = Toolbar(self)
        self.addWidget(toolbar)

        toolbar.add_button("settings", Toolbar.LEFT, "settings")
        toolbar.add_label("title", Toolbar.CENTER, "BP Chat")
        toolbar.add_button("search", Toolbar.RIGHT, "search").clicked.connect(
            lambda *args: toolbar.set_page("search"))

        toolbar.add_page("search")
        toolbar.add_button("back", Toolbar.LEFT, "arrow_back", page='search').clicked.connect(
            lambda *args: toolbar.set_page("first"))
        toolbar.add_input("input", Toolbar.CENTER, page='search')

        buttons_group = toolbar.add_buttons_group("buttons", part=Toolbar.BOTTOM)
        buttons_group.add_button("all", "all", "All")
        buttons_group.add_button("groups", "group", "Groups")
        buttons_group.add_button("contacts", "profile", "Contacts")

        self.toolbar = toolbar

        list_view = ListView(self)
        self.addWidget(list_view)

        update_button = QPushButton("Update")
        self.addWidget(update_button)

        self.list_model = ChatsModel(list_view)
        self.list_view = list_view

        self.setMinimumWidth(300)

    def paintEvent(self, QPaintEvent):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        start_color = QColor('#777777')
        start_color.setAlphaF(0.5)

        painter.setBrush(QBrush(start_color))
        painter.drawRect(QRect(QPoint(self.width()-1, 60), QPoint(self.width()-1, self.height())))

        painter.setBrush(QBrush(QColor('#ffc107')))
        painter.drawRect(QRect(QPoint(self.width()-1, 0), QPoint(self.width()-1, 59)))

