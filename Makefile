.PHONY: activate test setup

test:
	PYTHONPATH=./src python -m unittest discover tests

setup:
	pip install -r requirements.txt
