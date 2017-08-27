# magicscan
Scan and recognize Magic the Gathering cards


## Setup
You'll need Python 2.7, OpenCV, and Tesseract OCR.
On Mac OS it's helpful to use a virtual environment to avoid package collisions:

```
virtualenv env
source bin/activate
```

Run pip install dependent packages:
```
pip install -r requirements.txt`
```

## Running
```
python src/ocr.py -i images/140.jpg -a text
```


## References

1. http://opencv.org/
2. https://github.com/tesseract-ocr/tesseract
3. https://github.com/mtgjson/mtgjson
4. http://magiccards.info/query?q=wolf&v=card&s=cname

