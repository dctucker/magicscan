from PIL import Image
from bunch import Bunch
import pytesseract
import argparse
import cv2
import os
import json
from difflib import SequenceMatcher
from operator import itemgetter

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to input image to be OCR'd")
args = vars(ap.parse_args())


def CardImage:
	def __init__(self, filename):
		self.image = cv2.imread(filename)
		self.image = cv2.resize(image, None, fx = 4, fy = 4, interpolation = cv2.INTER_CUBIC)
		self.image = cv2.fastNlMeansDenoisingColored(self.image, None, 10, 10, 7, 21)
		self.temp_filename = "{}.png".format(os.getpid())

	def segment_and_scan(self, filename):
		"""Segment, preprocess, and OCR-scan an image given a filename
		
		returns a dict with text from each segment
		"""
		h, w, channels = self.image.shape

		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		#gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

		title, title_image = crop_segment( 0.04, 0.02, 0.85, 0.04 )
		title = title.split("\n")[0]

		description, description_image = gray[ int(0.63 * h):int(0.93 * h), int(0.05 * w):int(0.95 * w) ]
		cv2.imwrite(filename, description_image)
		text = pytesseract.image_to_string(Image.open(filename))
		description = text
		os.remove(filename)

		series_image = gray[ int(0.93 * h):, 0:int(0.2 * w) ]
		series_image = cv2.resize(series_image, None, fx = 4, fy = 4, interpolation = cv2.INTER_CUBIC)
		cv2.imwrite(filename, series_image)
		text = pytesseract.image_to_string(Image.open(filename))
		#series = text.split("\n")[0].split("/")
		series = text
		os.remove(filename)

		cv2.imshow("Title", title_image)
		cv2.imshow("Description", description_image)
		cv2.imshow("Series", series_image)
		#cv2.waitKey(0)

		return {'title': title, 'description': description, 'series': series}

	def crop_segment(self, left, top, right, bottom):
		cropped = gray[ int(top * h):int(bottom * h), int(left * w):int(right * w) ]
		cv2.imwrite(self.temp_filename, cropped)
		text = pytesseract.image_to_string(Image.open(self.temp_filename))
		title = text.split("\n")[0]
		os.remove(self.temp_filename)
		return text, cropped


class CardDb:
	def __init__(self, filename):
		with open(filename) as f:
			self.cards = json.load(f)


	def scan_database(self, search):
		"""Scan for a card in the database given attributes to search

		search should be an array of triples [(attr to search, search string, weight)]
		returns [(ratio, card), ...]
		"""
		matches = []

		def similarity(a, b):
			return SequenceMatcher(None, a, b).ratio()

		for name,card in self.cards.items():
			ratio = 0
			denom = 0
			for key,value,weight in search:
				if key in card:
					ratio += weight * similarity(value, card[key])
					denom += weight
				else:
					card[key] = None
			if denom > 1.0:
				ratio /= denom
			matches.append( (ratio, card,) )

		matches = sorted( matches, key=itemgetter(0), reverse=True )
		return matches


def print_matches(matches):
	for match in matches[0:5]:
		print "confidence =", match[0]
		print "name =", match[1]['name']
		print "text =", match[1]['text']
		print


scan = CardImage(args["image"]).segment_and_scan()
print "Scanned text:"
print scan.title, '/', scan.description, '/', scan.series

if len(scan.title) < 4:
	title_weight = 0.01
elif len(scan.title) < 8:
	title_weight = 0.5
else:
	title_weight = 0.9

db = CardDb('data/AllCards.json')
matches = db.scan_database([('name', scan.title, title_weight), ('text', scan.description, 1.0)])
print "Matches:"
print_matches(matches)
