.PHONY: activate test setup

test:
	python -m unittest discover tests

setup:
	pip install -r requirements.txt
