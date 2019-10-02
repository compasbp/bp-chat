from ..core.animate import *
from ..core.widgets import *
from ..models.list_model import ListView, ListModel, ListModelItem


class LeftWidget(VLayoutWidget):

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

        self.toolbar = toolbar

        list_view = ListView(self)
        self.addWidget(list_view)

        update_button = QPushButton("Update")
        self.addWidget(update_button)

        class Chat(ListModelItem):

            def __init__(self, title):
                self.title = title

            def getName(self):
                return self.title

            def getSecondText(self):
                return 'Some text...'

            def getTimeString(self):
                return '11:00'

            def getPixmap(self):
                return None

            def getBadgesCount(self):
                return 3

        items = [
            Chat("Chat #1"),
            Chat("Chat #2"),
            Chat("Chat #3"),
        ]
        list_model = ListModel(list_view, items)

        self.list_view = list_view

