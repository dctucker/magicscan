import os
import json
from operator import itemgetter
import cv2
import numpy as np
from decorators import *
from difflib import SequenceMatcher

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


class SymbolDB:
	@timed("Load image")
	def __init__(self):
		path = 'data/symbols/png'
		self.files = ('rtr.png','bng.png','fut.png','bcore.png','all.png','soi.png','unh.png')
		self.files = [ f for f in os.listdir(path) if ".png" in f ]
		self.images = {}
		self.contours = {}

		for filename in self.files:
			key = filename.replace(".png", "")
			image = cv2.imread(path+"/"+filename, cv2.IMREAD_UNCHANGED)
			alpha = cv2.split(image)[-1]
			image[:,:,0] = alpha
			image[:,:,1] = alpha
			image[:,:,2] = alpha
			image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			#image = cv2.resize(image, None, fx = 0.5, fy = 0.5)
			#image = cv2.GaussianBlur(image, (5,5), 10.0)
			#image = cv2.split(image)[-1]
			#image = image.convertTo( cv2.CV_8U )
			#laplace = cv2.Laplacian( image, cv2.CV_64F, cv2.CV_16S, 5 )
			#image = cv2.convertScaleAbs( laplace )
			self.images[ key ] = image

			_, contours, hierarchy = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
			self.contours[key] = contours[0]

	@timed("Matching templates")
	def match_templates(self, image):
		matches = []
		for series, template in self.images.items():
			template = self.images[ series ]
			res = cv2.matchTemplate(image, template,  cv2.TM_CCOEFF_NORMED)
			matches += [( np.max( res ), series, res )]
		return sorted( matches, key=itemgetter(0), reverse=True )

	@timed("Matching contours")
	def match_contours(self, contours):
		#TODO multiple contour mapping
		matches = []
		for series, template in self.images.items():
			template = self.images[ series ]
			res = cv2.matchShapes( contours, self.contours[series], 1, 0.0 )
			matches += [( np.max( res ), series, res )]
		return sorted( matches, key=itemgetter(0))

	def show_determination(self, matches):
		count = 0
		for ratio,series,res in matches:
			print (ratio,series,),

			count += 1
			if count < 10:
				filename = series + ".png"
				cv2.imshow(series, res)
				cv2.imshow(filename, self.images[series])
				cv2.moveWindow(series, count * 140, 20 )
				cv2.moveWindow(filename, count * 140, 200 )
