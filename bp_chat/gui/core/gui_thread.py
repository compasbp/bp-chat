from PyQt5.QtCore import QObject, pyqtSignal


def to_gui_thread(func):

    def _new_func(*args, **kwargs):
        _toGuiControlObject.signal.emit(func, args, kwargs)

    return _new_func


class _ToGuiControlObject(QObject):

    signal = pyqtSignal(object, tuple, dict)

    def __init__(self):
        super().__init__()

        self.signal.connect(self.slot)

    def slot(self, func, args, kwargs):
        func(*args, **kwargs)


_toGuiControlObject = _ToGuiControlObject()

