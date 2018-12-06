import unittest 				# import pyhton standard library for unit testing
from server import Board 		# import the module we want to test


class TestServer(unittest.TestCase):

    def setUp(self):		# must be camleCased
        self.board = Board()

    def tearDown(self): 	# must be camleCased
        pass

    def test_add(self):
        self.board.add(0, "ip1", 1)
        self.board.add(1, "b", 10)
        self.board.add(2, "c", 10)
        print(self.board.getEntries())
        self.assertEqual(len(self.board.getEntries()), 3)

    def test_delete(self):
        self.board.add(0, "a", 10)
        self.board.delete(0, 10)
        self.assertEqual(len(self.board.getEntries()), 0)
        self.board.add(1, "b", 10)
        self.board.getEntries()
        self.assertEqual(len(self.board.getEntries()), 1)

    def test_modify(self):
        self.board.add(0, "a", 10)
        self.board.add(1, "b", 10)
        self.board.modify(0, 10, "b")
        val = self.board.getEntries()[0][0][1]
        self.assertTrue(val, 10)

    def test_delQueue(self):
        self.board.delete(0, 10)
        self.board.add(0, "a", 10)
        self.assertEqual(len(self.board.getEntries()), 0)

    def test_modQueue(self):
        self.board.modify(0, 10, "b")
        self.board.add(0, "a", 10)
        self.assertEqual(self.board.getEntries()[0][0][1], 'b')


if __name__ == '__main__':
    unittest.main()
