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

def scan_image(filename):
	# load the image, resize to 2x, convert to grayscale
	image = cv2.imread(filename)
	image = cv2.resize(image, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	 
	# apply threshold or blur
	if args["preprocess"] == "thresh":
		gray = cv2.threshold(gray, 0, 255,
			cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
	elif args["preprocess"] == "blur":
		gray = cv2.medianBlur(gray, 3)
	 
	# write grayscale image to disk as a temporary file for ORC
	filename = "{}.png".format(os.getpid())
	cv2.imwrite(filename, gray)

	# debug: show images
	#cv2.imshow("Image", image)
	#cv2.imshow("Output", gray)
	#cv2.waitKey(0)

	# load the image as a PIL/Pillow image
	text = pytesseract.image_to_string(Image.open(filename))
	os.remove(filename)
	text = text.replace("\n", " ")
	text = text.replace("  ", " ")
	text = text.replace("- ", "-")
	return text

def segment_and_scan(filename):
	image = cv2.imread(filename)
	image = cv2.resize(image, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
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
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	#gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

	title_image = gray[ 0:int(0.10 * h), int(0.04 * w):int(0.85 * w) ] 
	cv2.imwrite(filename, title_image)
	text = pytesseract.image_to_string(Image.open(filename))
	title = text.split("\n")[0]
	os.remove(filename)

	description_image = gray[ int(0.63 * h):int(0.93 * h), int(0.05 * w):int(0.95 * w) ]
	cv2.imwrite(filename, description_image)
	text = pytesseract.image_to_string(Image.open(filename))
	description = text
	os.remove(filename)

	cv2.imshow("Title", title_image)
	cv2.imshow("Description", description_image)
	#cv2.waitKey(0)

	return title, description


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
title, description = segment_and_scan(args["image"])
print "Scanned text:"
print title, '/', description
#print
matches = scan_database([('name', title, 1.0), ('text', description, 0.25)])
print "Matches:"
print_matches(matches)
