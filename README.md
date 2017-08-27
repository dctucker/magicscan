# magicscan
Scan and recognize Magic the Gathering cards


## Setup
You'll need Python 2.7, OpenCV, and Tesseract.
On Mac OS it's helpful to use a virtual environment to avoid package collisions:

virtualenv env
source bin/activate

Run pip install dependent packages:

pip install -r requirements.txt

## Running

python ocr.py -i 140.jpg -a text


## References

1. https://github.com/mtgjson/mtgjson
2. http://magiccards.info/query?q=wolf&v=card&s=cname
