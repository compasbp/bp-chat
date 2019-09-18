from unittest import main as unittest_main, TestCase

from bp_chat.logic.common.tryable import run_in_try
from bp_chat.logic.common.app import App


class TestConsole(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = App.instance()

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

    def test_run_in_try(self):
        run_in_try(self.produce_exception)

    def test_run_in_try_2(self):
        run_in_try(self.produce_exception)

    def produce_exception(self):
        raise Exception('exception')


class TestConsole2(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = App.instance()

    @classmethod
    def tearDownClass(cls):
        cls.app.close()

    def test_run_in_try(self):
        run_in_try(self.produce_exception)

    def produce_exception(self):
        raise Exception('exception 2')


if __name__=='__main__':
    unittest_main()
