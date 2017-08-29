from PIL import Image
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
ap.add_argument("-a", "--attr", type=str, default="name",
	help="attribute to search on")
ap.add_argument("-p", "--preprocess", type=str, default="thresh",
	help="type of preprocessing to be done")
args = vars(ap.parse_args())

def segment_and_scan(filename):
	image = cv2.imread(filename)
	image = cv2.resize(image, None, fx = 4, fy = 4, interpolation = cv2.INTER_CUBIC)
	h, w, channels = image.shape
	filename = "{}.png".format(os.getpid())

	#contours,hierarchy = cv2.findContours(0,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
	#cnt = contours[0]
	#x,y,w,h = cv2.boundingRect(cnt)

	#lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
	#l, a, b = cv2.split(lab)
	#clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
	#cl = clahe.apply(l)
	#gray = cl
	image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	#gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

	title_image = gray[ int(0.02 * h):int(0.10 * h), int(0.04 * w):int(0.85 * w) ]
	cv2.imwrite(filename, title_image)
	text = pytesseract.image_to_string(Image.open(filename))
	title = text.split("\n")[0]
	os.remove(filename)

	description_image = gray[ int(0.63 * h):int(0.93 * h), int(0.05 * w):int(0.95 * w) ]
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


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def scan_database(search):
	matches = []

	with open('data/AllCards.json') as f:
		cards = json.load(f)

		for name,card in cards.items():
			ratio = 0
			denom = 0
			for key,value,weight in search:
				if key in card:
					ratio += weight * similarity(value, card[key])
					denom += weight
			if denom > 1.0:
				ratio /= denom
			matches.append( (ratio, card,) )

	matches = sorted( matches, key=itemgetter(0), reverse=True )
	return matches

def print_matches(matches):
	for match in matches[0:5]:
		print "confidence =", match[0]
		print "name =", match[1]['name']
		print args['attr'], '=', match[1][args['attr']]
		print

#text = scan_image(args["image"])
scanned = segment_and_scan(args["image"])
locals().update(scanned)
print "Scanned text:"
print title, '/', description, '/', series

if len(title) < 4:
	title_weight = 0.01
elif len(title) < 8:
	title_weight = 0.5
else:
	title_weight = 0.9
#print
matches = scan_database([('name', title, title_weight), ('text', description, 1.0)])
print "Matches:"
print_matches(matches)
