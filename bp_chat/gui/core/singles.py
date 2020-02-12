from json import dumps, loads
from threading import Timer
from copy import copy
from os.path import exists, dirname
from os import makedirs
from ...core.app_common import get_app_dir_path_with_uuid_suf


class MessagesForSend:

    connectedEditor = None
    chat_id = None
    save_timer = None
    last_saved = None

    def __init__(self, path_fo_json=None):
        self.path_fo_json = path_fo_json or (get_app_dir_path_with_uuid_suf()+'/frsnd.json')
        _dir = dirname(self.path_fo_json)
        if not exists(_dir):
            makedirs(_dir)
        self.load_json()

    def updateMessageEditor(self, textEditor, chat_id):
        if chat_id == None:
            return
        chat_id = str(chat_id)
        self.chat_id = chat_id
        if not self.connectedEditor:
            self.connectedEditor = textEditor
            textEditor.textChanged.connect(self.textChanged)
        text = self.connectedEditor.toPlainText()
        last_text = self.data.get(chat_id)
        if text != last_text:
            self.connectedEditor.setPlainText(last_text)

    def textChanged(self):
        text = self.connectedEditor.toPlainText()
        #print("TTT:", self.chat_id, type(self.chat_id), text)
        self.data[self.chat_id] = text
        if self.save_timer:
            self.save_timer.cancel()
        self.save_timer = Timer(3, self.save_json)
        self.save_timer.start()

    def save_json(self):
        print('[ save_json ] {}'.format(self.path_fo_json))
        if self.last_saved != self.data:
            self.last_saved = copy(self.data)
            with open(self.path_fo_json, 'w', encoding='utf-8') as f:
                f.write(dumps(self.last_saved))

    def load_json(self):
        print('[ load_json ] {}'.format(self.path_fo_json))
        try:
            with open(self.path_fo_json, encoding='utf-8') as f:
                self.data = loads(f.read())
        except BaseException as e:
            print('error: {}'.format(e))
            self.data = {}