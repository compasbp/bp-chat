from threading import Thread
from queue import Queue
from time import sleep
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


class Action:

    started = False
    cancelled = False
    _percent = -1
    _last_percent_time = None

    def start(self):
        if self.cancelled:
            self.on_cancelled()
            return
        self.started = True
        self.on_started()
        self.run()
        if not self.cancelled:
            self.on_finished()

    def cancel(self):
        self.cancelled = True
        if self.started:
            self.on_cancelled()

    @property
    def percent(self):
        return self._percent

    @percent.setter
    def percent(self, val):
        last = self._percent
        if val != last:
            _last_percent_time = self._last_percent_time
            now = datetime.now()
            if not self._last_percent_time or (now - _last_percent_time).total_seconds() >= 0.3:
                self._last_percent_time = now
                self._percent = val
                self.on_percent(val)

    def run(self):
        pass

    def on_started(self):
        pass

    def on_finished(self):
        pass

    def on_cancelled(self):
        pass

    def on_percent(self, val):
        pass


class ActionGroup(Action):

    def __init__(self, *actions):
        self.actions = actions if actions else []

    def append(self, action):
        self.actions.append(action)

    def run(self):
        with ThreadPoolExecutor(max_workers=len(self.actions)) as executor:
            futures = {
                executor.submit(action.start): action
                for action in self.actions
            }

            for _ in as_completed(futures):
                pass

    def cancel(self):
        for a in self.actions:
            a.cancel()
        super().cancel()


class ActionsQueue:

    RUN_TIMEOUT = 0.1

    __instance = None
    may_work = False

    @staticmethod
    def instance(may_work=None, instance_id=0):
        if may_work != None:
            ActionsQueue.may_work = may_work

        if not ActionsQueue.may_work:
            return ActionsQueueNull

        if not ActionsQueue.__instance:
            ActionsQueue.__instance = ActionsQueue(instance_id)
            ActionsQueue.__instance.start()

        return ActionsQueue.__instance

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.queue = Queue()

    def append(self, action):
        self.queue.put(action)

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    @staticmethod
    def stop():
        instance = ActionsQueue.instance()
        ActionsQueue.may_work = False
        ActionsQueue.__instance = None
        return instance

    def join(self):
        self.thread.join()

    def run(self):
        q = self.queue

        while ActionsQueue.may_work:
            while not q.empty():
                action = q.get()
                action.start()

            sleep(ActionsQueue.RUN_TIMEOUT)

        while not q.empty():
            action = q.get()
            action.start()


class ActionsQueueNull:

    @staticmethod
    def append(action):
        pass