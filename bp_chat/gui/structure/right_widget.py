from ..core.animate import *
from ..core.widgets import *
from ..models.list_model import ListView, MessagesListModel
from PyQt5.QtWidgets import QAbstractItemView


class RightWidget(VLayoutWidget):

    def __init__(self, app, splitter, left_widget):
        super().__init__(splitter)

        self.left_widget = left_widget

        toolbar = Toolbar(self)
        self.addWidget(toolbar)

        set_widget_background(self, "#ffffff")

        def _show(*args):
            # w.a = fix_window(AnimatedDialog(w))
            # w.a.resize(200, 200)
            # w.a.exec_()
            pass

        toolbar.add_label("clear", Toolbar.CENTER, '')
        toolbar.add_page("chat")
        # toolbar.add_button("back", Toolbar.LEFT, "arrow_back", page='search').clicked.connect(
        #     lambda *args: toolbar.set_page("first"))
        # toolbar.add_input("input", Toolbar.CENTER, page='search')

        toolbar.add_button("group", Toolbar.LEFT, "group", page='chat')
        toolbar.add_label("title", Toolbar.CENTER, 'Title', page='chat')
        #toolbar.add_button("menu", Toolbar.RIGHT, "menu").clicked.connect(_show)

        buttons_group = toolbar.add_buttons_group("right_buttons", to=Toolbar.RIGHT, page='chat')
        self.menu_button = buttons_group.add_button("menu", "menu")
        self.menu_button.clicked.connect(self.open_chat_menu)
        buttons_group.add_button("cancel", "cancel").clicked.connect(self.close_chat)

        # info_label = InfoLabel(self)
        # info_label.setText("Some info...")
        # self.addWidget(info_label)

        #self.lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.toolbar = toolbar

        paged_widget = self.paged_widget = PagedWidget(self)
        self.addWidget(paged_widget)

        paged_widget.add_page('clear', VLayoutWidget())
        chat_page: VLayoutWidget = paged_widget.add_page('chat', VLayoutWidget())

        list_view = ListView()
        list_view.setSelectionMode(QAbstractItemView.NoSelection) # QAbstractItemView.MultiSelection
        chat_page.addWidget(list_view)

        self.list_model = MessagesListModel(list_view)
        self.list_view = list_view

        self.message_input = MessageInputWidget()
        chat_page.addWidget(self.message_input)

        self.setMinimumWidth(500)

    def open_chat(self, chat):
        self.toolbar.set_page('chat')
        self.toolbar.set_text('title', chat.title)
        self.list_model.items_dict = chat.messages
        self.list_model.reset_model()
        self.paged_widget.set_page('chat')
        self.toolbar.down_shadow.raise_()

    def close_chat(self):
        self.toolbar.set_page('first')
        self.list_model.items_dict = {}
        self.list_model.reset_model()
        self.paged_widget.set_page('clear')
        self.left_widget.list_view.clear_selection()

    def open_chat_menu(self):
        global_pos = self.menu_button.mapToGlobal(self.menu_button.pos())
        self.left_widget.list_view.open_menu_for_selected_item(QPoint(global_pos.x(), global_pos.y()+self.menu_button.height()))
