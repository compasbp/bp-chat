from unittest import main as unittest_main, TestCase
from time import sleep
from datetime import datetime

from bp_chat.core.action import ActionsQueue, Action, ActionGroup


class TestConsole(TestCase):

    actions_queue: ActionsQueue

    @classmethod
    def setUpClass(cls):
        cls.actions_queue = ActionsQueue.instance(may_work=True)

    @classmethod
    def tearDownClass(cls):
        cls.actions_queue.stop()

    def test_1(self):

        class Action1(Action):

            def __init__(self, num):
                self.num = num

            def run(self):
                for a in range(0, 100, 10):
                    if self.cancelled:
                        return
                    self.percent = a
                    sleep(0.1)

            def on_started(self):
                print('[start-{}] {}'.format(self.num, datetime.now()))

            def on_finished(self):
                print('[fin-{}] {}'.format(self.num, datetime.now()))

            def on_cancelled(self):
                print('[cancelled-{}] {}'.format(self.num, datetime.now()))

            def on_percent(self, val):
                print(f'\t{val}% ({self.num})')

        self.actions_queue.append(Action1(1))
        self.actions_queue.append(Action1(2))
        a3 = Action1(3)
        a4 = Action1(4)
        self.actions_queue.append(a3)
        self.actions_queue.append(a4)

        a5 = ActionGroup(Action1(5), Action1(6))
        self.actions_queue.append(a5)

        sleep(2.5)

        a3.cancel()
        a4.cancel()

        sleep(1.5)

# class Test2(TestCase):
#
#     def test_2(self):
#         def run(num):
#             print(f'[start] {num}')
#             sleep(1)
#             return True
#
#         with ThreadPoolExecutor(max_workers=1) as executor:
#             futures = {
#                 executor.submit(run, num): num
#                 for num in range(3)
#             }
#
#             for future in as_completed(futures):
#                 num = futures[future]
#                 data = future.result()
#                 print(f'[fin] {num} -> {data}')

if __name__=='__main__':
    unittest_main()
