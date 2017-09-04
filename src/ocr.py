from PIL import Image, ImageGrab
from bunch import Bunch
import pytesseract
import argparse
import cv2
import os
from db import *
from difflib import SequenceMatcher
import sys
from decorators import *
import numpy as np


# TODO find logging library so we can set it to error,warn,info,debug levels

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

		self.gray = cv2.resize(self.gray, None, fx = 1.4, fy = 1.4, interpolation = cv2.INTER_CUBIC)
		print "symbol...",
		#symbol_image = self.crop_segment( 0.85, 0.55, 0.99, 0.65 )
		symbol_image = self.crop_segment( 0.87, 0.572, 0.955, 0.615 )
		#gaussian_3 = cv2.GaussianBlur(symbol_image, (9,9), 10.0)
		#symbol_image = cv2.addWeighted(symbol_image, 1.5, gaussian_3, -0.5, 0, symbol_image)
		#symbol_image = cv2.resize(symbol_image, (138, 138), interpolation = cv2.INTER_CUBIC)
		blur = cv2.GaussianBlur(symbol_image,(3,3),11)
		_, symbol_image = cv2.threshold(blur, 128, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
		#symbol_image = cv2.adaptiveThreshold(symbol_image, 240, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
		symbol_image = 255 - symbol_image
		symbol_image = cv2.copyMakeBorder(symbol_image,100,100,100,100,cv2.BORDER_CONSTANT,value=(0,0,0))
		
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

			matches = symbol_db.determine_series( symbol_image )
			count = 0
			for ratio,series,res in matches:
				print (ratio,series,),

				count += 1
				if count < 10:
					filename = series + ".png"
					cv2.imshow(series, res)
					cv2.imshow(filename, symbol_db.images[series])
					cv2.moveWindow(series, count * 140, 20 )
					cv2.moveWindow(filename, count * 140, 200 )


			print
			cv2.waitKey(0)
			print "Press any key to continue...",
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

