from datetime import datetime

from .core.animate import *
from .core.widgets import *
from .models.model_items import ChatItem, MessageItem
from .structure.left_widget import LeftWidget
from .structure.right_widget import RightWidget
from bp_chat.logic.data import ServerData, User, Chat, Message


def main():
    app = QApplication([])

    users = {
        1: User(1, 'wind'),
        2: User(2, 'serg'),
        3: User(3, 'Lev'),
    }
    server_data = ServerData(users=users, chats={
        1: Chat(1, 'Test chat 1', [], {
            1: Message(id=1, sender=users[1], chat=None, text="Hello 1!", datetime=datetime.now()),
            2: Message(id=2, sender=users[2], chat=None, text="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", datetime=datetime.now()),
            3: Message(id=3, sender=users[1], chat=None, text="Hello 3!", datetime=datetime.now()),
        }),
        2: Chat(2, 'Test chat 2', [], {}),
        3: Chat(3, 'Test chat 3', [], {}),
    })

    w = main_widget(QWidget())
    w.resize(800, 600)
    main_lay = QVBoxLayout(w)
    main_lay.setContentsMargins(0, 0, 0, 0)

    splitter = LeftRightSplitter(w)
    main_lay.addWidget(splitter)

    left_widget = LeftWidget(splitter)
    left_widget.list_model.model_item = ChatItem
    left_widget.list_model.items_dict = server_data.chats
    right_widget = RightWidget(app, splitter)
    right_widget.list_model.model_item = MessageItem
    right_widget.list_model.items_dict = server_data.chats[1].messages

    def on_chat_selected(selected_chats):
        if selected_chats:
            chat = selected_chats[0].chat
            right_widget.toolbar.set_text('title', chat.title)
            right_widget.list_model.items_dict = server_data.chats[chat.id].messages
            right_widget.list_model.reset_model()

    left_widget.list_view.set_selected_callback(on_chat_selected)

    splitter.add_widget(left_widget, LeftRightSplitter.LEFT)
    splitter.add_widget(right_widget, LeftRightSplitter.RIGHT)
    splitter.setSizes([100, 200])

    w.show()

    tray_icon = SystemTrayIcon(favicon(), w, app)
    tray_icon.show()
    # tray_icon.raise_()
    tray_icon.showMessage("BP Chat is started", "Hello!", favicon())

    app.exec_()