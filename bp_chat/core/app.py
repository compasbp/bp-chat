
from .tryable import ConsoleThread, run_in_try
from .action import ActionsQueue


def as_app(func):

    def _new_func():
        run_app(func)

    return _new_func


def run_app(func):
   app = App.instance()

   run_in_try(lambda: func(app))

   app.close()


class App:

    __instance = None
    __instance_count = 0
    _main_widget = None
    console = None

    @staticmethod
    def instance():
        if not App.__instance:
            App.__instance_count += 1
            App.__instance = App(App.__instance_count)
        return App.__instance

    def __init__(self, instance_id):
        self.__instance_id = instance_id
        self.console = ConsoleThread.instance(True, instance_id)
        ActionsQueue.instance(True, instance_id)

    @property
    def main_widget(self):
        return self._main_widget

    @main_widget.setter
    def main_widget(self, value):
        self._main_widget = value

    def close(self):
        console = ConsoleThread.stop()
        ActionsQueue.stop()
        App.__instance = None
        console.join()
