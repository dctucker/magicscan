import json
from decorators import *

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

