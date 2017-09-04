from PIL import Image, ImageGrab
from bunch import Bunch
import pytesseract
import argparse
import cv2
import os
import json
from difflib import SequenceMatcher
from operator import itemgetter
import sys
from decorators import *
import numpy as np


# TODO find logging library so we can set it to error,warn,info,debug levels

class SymbolDB:
	@timed("Load image")
	def __init__(self):
		path = 'data/symbols/png'
		self.files = ('bcore.png','all.png','soi.png','unh.png')
		self.files = [ f for f in os.listdir(path) if ".png" in f ]
		self.images = {}
		for filename in self.files:
			key = filename.replace(".png", "")
			image = cv2.imread(path+"/"+filename, cv2.IMREAD_UNCHANGED)
			print image.shape
			alpha = cv2.split(image)[-1]
			image[:,:,0] = alpha
			image[:,:,1] = alpha
			image[:,:,2] = alpha
			image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			image = cv2.GaussianBlur(image, (9,9), 10.0)
			#image = cv2.split(image)[-1]
			#image = image.convertTo( cv2.CV_8U )
			#image = cv2.Laplacian( image, cv2.CV_64F )
			cv2.imshow(filename, image)
			self.images[ key ] = image

	@timed("Determining series")
	def determine_series(self, image):
		matches = []
		for series, template in self.images.items():
			#for series in ('soi','unh'):
			template = self.images[ series ]
			#res = cv2.bitwise_xor( image , template )
			res = cv2.matchTemplate(image, template,  cv2.TM_CCOEFF)
			cv2.imshow(series, res.copy())
			matches += [( np.sum( res ), series )]
		return sorted( matches, key=itemgetter(0), reverse=True )

symbol_db = SymbolDB()

class CardImage:
	@timed("Load image")
	def __init__(self, filename, show_crops=False, do_ocr=True):
		self.image = cv2.imread(filename)
		self.image = cv2.resize(self.image, None, fx = 4, fy = 4, interpolation = cv2.INTER_CUBIC)
		self.temp_filename = "{}.png".format(os.getpid())

		self.gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
		self.gray = cv2.fastNlMeansDenoising(self.gray, None, 10)
		#self.gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
		#self.gray = self.image

		self.show_crops = show_crops
		self.do_ocr = do_ocr

	def segment_and_scan(self):
		"""Segment, preprocess, and OCR-scan an image given a filename
		
		returns a dict with text from each segment
		"""

		# croping images

		print "Segmenting image...",
		print "title...",
		title_image = self.crop_segment( 0.04, 0.01, 0.85, 0.10 )
		print "description...",
		description_image = self.crop_segment( 0.05, 0.63, 0.99, 0.93 )
		print "type...",
		type_image = self.crop_segment( 0.05, 0.55, 0.85, 0.63 )

		self.gray = cv2.resize(self.gray, None, fx = 1.5, fy = 1.5, interpolation = cv2.INTER_CUBIC)
		print "symbol...",
		#symbol_image = self.crop_segment( 0.88, 0.57, 0.955, 0.615 )
		symbol_image = self.crop_segment( 0.85, 0.55, 0.99, 0.65 )
		#gaussian_3 = cv2.GaussianBlur(symbol_image, (9,9), 10.0)
		#symbol_image = cv2.addWeighted(symbol_image, 1.5, gaussian_3, -0.5, 0, symbol_image)
		#symbol_image = 255 - symbol_image
		#symbol_image = cv2.resize(symbol_image, (138, 138), interpolation = cv2.INTER_CUBIC)
		symbol_image = cv2.equalizeHist(symbol_image)
		symbol_image = cv2.adaptiveThreshold(symbol_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)
		
		#symbol_image = cv2.threshold(symbol_image, 240, 255, cv2.THRESH_BINARY)

		print "series...",
		series_image = self.crop_segment( 0, 0.93, 0.2, 1 )

		print "done!"
		
		if self.show_crops:
			print "Displaying cropped segments...",
			cv2.imshow("Title", title_image)
			cv2.imshow("Description", description_image)
			cv2.imshow("Series", series_image)
			cv2.imshow("Symbol", symbol_image)
			cv2.imshow("Type", type_image)
			sw, sh = ImageGrab.grab().size
			cv2.moveWindow("Title",        sw/3, int(sh*0.1) )
			cv2.moveWindow("Description",  sw/3, int(sh*0.3) )
			cv2.moveWindow("Series",       sw/3, int(sh*0.7) )
			cv2.moveWindow("Type",         sw/3, int(sh*0.2) )
			cv2.moveWindow("Symbol",    sw-sw/4, int(sh*0.2) )
			print "Press any key to continue...",
			print symbol_db.determine_series( symbol_image )
			cv2.waitKey(0)
			print "good job!"



		if self.do_ocr:
			print "Recognizing characters, optically...",
			print "title...",
			title = self.scan_segment(title_image)
			title = title.split("\n")[0]

			print "description...",
			description = self.scan_segment(description_image)
			
			print "series...",
			series = self.scan_segment(series_image)
			#series = series.split("\n")[0].split("/")

			print "type...",
			cardType = self.scan_segment(type_image)
			print "done!"

			if len(title) < 4:
				title_weight = 0.01
			elif len(title) < 8:
				title_weight = 0.5
			else:
				title_weight = 0.9

			return {
				'title': title,
				'description': description,
				'weights': {
					'title': title_weight,
					'description': 1.0,
					'type': 1.0 #TODO make sure this is correct
				},
				'type': cardType,
				'series': series
			}
		
		return None

	def crop_segment(self, left, top, right, bottom):
		h, w = self.gray.shape
		h -= 1
		w -= 1
		cropped = self.gray[ int(top * h):int(bottom * h), int(left * w):int(right * w) ]
		return cropped.copy()

	@timed("OCR")
	def scan_segment(self, cropped):
		cv2.imwrite(self.temp_filename, cropped)
		text = pytesseract.image_to_string(Image.open(self.temp_filename))
		os.remove(self.temp_filename)
		return text


class CardDb:
	@timed("Loading DB")
	def __init__(self, filename):
		with open(filename) as f:
			self.cards = json.load(f)

	@timed("Scanning DB")
	def scan_database(self, search):
		"""Scan for a card in the database given attributes to search

		search should be an array of triples [(attr to search, search string, weight)]
		returns [(ratio, card), ...]
		"""
		matches = []
		for name,card in self.cards.items():
			match = self.compare_card(card, search)
			if match[0] > 0.1:
				matches.append( match )

		matches = sorted( matches, key=itemgetter(0), reverse=True )
		return matches

	def compare_card(self, card, search):
		def similarity(a, b):
			return SequenceMatcher(None, a, b).ratio()

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

		return (ratio, card,)

	@classmethod
	def print_matches(cls, matches):
		for match in matches[0:5]:
			print "confidence =", match[0]
			print "name =", match[1]['name']
			print "text =", match[1]['text']
			print "type =", match[1]['type']
			print


if __name__ == '__main__':
	try:
		u'\u2014'.encode(sys.stdout.encoding)
	except UnicodeEncodeError as uee:
		# TODO improve this message
		print "Current encoding not supported. Use a terminal which supports unicode."
		print "for Windows, try 'chcp 1252'"
		sys.exit(0)

	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--image", required=True,
		help="path to input image to be OCR'd")
	ap.add_argument("-s", "--show-crops", required=False, action="store_true", default=False,
		help="show the image results of OCR")
	ap.add_argument("-ko", "--skip-ocr", required=False, action="store_false", default=True, dest="do_ocr",
		help="skips ocr scans")
	ap.add_argument("-kl", "--skip-lookup", required=False, action="store_false", default=True, dest="do_lookup",
		help="skips the database lookup")
	parsed_args = ap.parse_args()

	print "\nWelcome to MagicScan!"
	print "(or whatever we end up calling it)"
	print '\n', parsed_args
	args = vars(parsed_args)
	print "current encoding = ",sys.getdefaultencoding(),"\n"

	print "Loading image...",
	card_image = CardImage(args["image"], args["show_crops"], args["do_ocr"])
	print "done!"

	segments = card_image.segment_and_scan()
	hasScanData = segments is not None
	if hasScanData:
		scan = Bunch(segments)
		print "\nScanned text:"
		print scan.title, '/', scan.description, '/', scan.series, '/', scan.type

	if args["do_lookup"] and hasScanData:
		db = CardDb('data/AllCards.json')

		print "Scanning", len(db.cards), "cards..."
		matches = db.scan_database([
			('name', scan.title, scan.weights['title']),
			('text', scan.description, scan.weights['description']),
			('type', scan.type, scan.weights['type'])
			])
		print "done!"
		print "\nMatches:"
		CardDb.print_matches(matches)

