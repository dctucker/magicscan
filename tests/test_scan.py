import unittest
from ocr import *

class test_scan(unittest.TestCase):
	def test_scan(self):
		card_image = CardImage("images/2crop.jpg")
		scan = Bunch(card_image.segment_and_scan())
		db = CardDb('data/twocards.json')
		matches = db.scan_database([('name', scan.title, scan.weights['title']), ('text', scan.description, scan.weights['description'])])

		first = matches[0]
		self.assertGreater( first[0], 0.5 )
		self.assertEquals(  first[1]['name'], 'AWOL' )

if __name__ == '__main__':
	unittest.main()
