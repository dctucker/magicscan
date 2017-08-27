from PIL import Image
import pytesseract
import argparse
import cv2
import os
import json
from difflib import SequenceMatcher
from operator import itemgetter

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to input image to be OCR'd")
ap.add_argument("-a", "--attr", type=str, default="name",
	help="attribute to search on")
ap.add_argument("-p", "--preprocess", type=str, default="thresh",
	help="type of preprocessing to be done")
args = vars(ap.parse_args())

search_on_attr = args['attr']


# load the example image and convert it to grayscale
image = cv2.imread(args["image"])
image = cv2.resize(image, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
# check to see if we should apply thresholding to preprocess the
if args["preprocess"] == "thresh":
	gray = cv2.threshold(gray, 0, 255,
		cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
elif args["preprocess"] == "blur":
	gray = cv2.medianBlur(gray, 3)
 
# write the grayscale image to disk as a temporary file so we can
# apply OCR to it
filename = "{}.png".format(os.getpid())
cv2.imwrite(filename, gray)


# load the image as a PIL/Pillow image, apply OCR, and then delete
# the temporary file
text = pytesseract.image_to_string(Image.open(filename))
text = text.replace("\n", " ")
text = text.replace("  ", " ")
text = text.replace("- ", "-")
os.remove(filename)
print(text)


with open('data/AllCards.json') as f:
	cards = json.load(f)

matches = []
for name,card in cards.items():
	if 'text' in card:
		ratio = similar(text, card[search_on_attr])
		matches.append( (ratio, card,) )

matches = sorted( matches, key=itemgetter(0), reverse=True )
for match in matches[0:5]:
	print match[0], match[1]['name'],
	print search_on_attr, '=', match[1][search_on_attr],
	print

 
# show the output images
#cv2.imshow("Image", image)
cv2.imshow("Output", gray)
cv2.waitKey(0)

