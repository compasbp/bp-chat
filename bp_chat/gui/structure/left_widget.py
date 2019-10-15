from ..core.animate import *
from ..core.widgets import *
from ..core.draw import LoadAnimation
from ..models.list_model import ListView, ChatsModel


class LeftWidget(VLayoutWidget):

    MARGINS = (0, 0, 1, 0)

    def __init__(self, splitter, main_widget):
        super().__init__(splitter)

        toolbar = Toolbar(self)
        self.addWidget(toolbar)

        set_widget_background(self, '#ffffff')

        self.load_animation = LoadAnimation(self)

        def _loading(*args):
            self.paged_widget.set_page('clear')
            self.toolbar.set_page('settings')
            self.load_animation.stop()
            self.load_animation.start()

        toolbar.add_button("settings", Toolbar.LEFT, "settings").clicked.connect(_loading)
        toolbar.add_label("title", Toolbar.CENTER, "BP Chat")
        toolbar.add_button("search", Toolbar.RIGHT, "search").clicked.connect(
            lambda *args: toolbar.set_page("search"))

        toolbar.add_page("search")
        toolbar.add_button("back", Toolbar.LEFT, "arrow_back", page='search').clicked.connect(
            lambda *args: toolbar.set_page("first"))
        toolbar.add_input("input", Toolbar.CENTER, page='search')

        toolbar.add_page("settings")
        toolbar.add_button("settings_back", Toolbar.LEFT, "arrow_back", page='settings').clicked.connect(
            lambda *args: toolbar.set_page("first"))

        buttons_group = toolbar.add_buttons_group("buttons", part=Toolbar.BOTTOM)
        buttons_group.add_button("all", "all", "All")
        buttons_group.add_button("groups", "group", "Groups")
        buttons_group.add_button("contacts", "profile", "Contacts")

        self.toolbar = toolbar

        paged_widget = self.paged_widget = PagedWidget(self)
        self.addWidget(paged_widget)

        paged_widget.add_page('clear', VLayoutWidget())
        chats_page: VLayoutWidget = paged_widget.add_page('chats', VLayoutWidget())
        paged_widget.set_page('chats')

        list_view = ListView(self)
        chats_page.addWidget(list_view)

        update_button = QPushButton("Update")
        self.addWidget(update_button)

        self.list_model = ChatsModel(list_view)
        self.list_view = list_view

        self.setMinimumWidth(300)

        self.toolbar.down_shadow.raise_()

        self.right_shadow = SideShadow(main_widget, side=SideShadow.RIGHT, h=10)
        self.right_shadow.install(self)

    def paintEvent(self, QPaintEvent):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)

        start_color = QColor('#777777')
        start_color.setAlphaF(0.5)

        painter.setBrush(QBrush(start_color))
        painter.drawRect(QRect(QPoint(self.width()-1, 60), QPoint(self.width()-1, self.height())))

        painter.setBrush(QBrush(QColor('#999999'))) # #ffc107
        painter.drawRect(QRect(QPoint(self.width()-1, 0), QPoint(self.width()-1, 59)))

    # def showEvent(self, e):
    #     ret = super().showEvent(e)
    #     self.right_shadow.show()
    #     self.right_shadow.raise_()
    #     return ret

