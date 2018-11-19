import unittest 				# import pyhton standard library for unit testing 
from server import Board 		# import the module we want to test

class TestServer(unittest.TestCase):

	def setUp(self):		# must be camleCased
		self.board = Board()

	def tearDown(self): 	# must be camleCased
		pass


	def test_add(self):
		self.assertEqual(self.board.add("a"),0)
		self.assertEqual(self.board.add("b"),1)
		self.assertEqual(self.board.add("c"),2)

	def test_delete(self):
		self.board.add("a")
		self.board.delete(0)
		self.assertEqual(self.board.add("b"),1)
		self.assertEqual(self.board.getEntries().get(1),"b")


	def test_modify(self):
		self.board.add("a")
		self.board.modify(0,"b")
		self.assertEqual(self.board.getEntries().get(0),"b")

	def test_getEntries(self):
		self.board.add("a")
		self.assertEqual(self.board.getEntries().get(0),"a")


if __name__ == '__main__':
	unittest.main()