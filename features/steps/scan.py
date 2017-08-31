from behave import *
from src.ocr import *
from hamcrest import *

@given(u'an image "{filename}"')
def step_impl(context, filename):
	context.card_image = CardImage("images/2crop.jpg")

@when(u'the image is scanned')
def step_impl(context):
	scan = Bunch(context.card_image.segment_and_scan())
	db = CardDb('data/twocards.json')
	matches = db.scan_database([('name', scan.title, scan.weights['title']), ('text', scan.description, scan.weights['description'])])
	context.match = matches[0]

@then(u'the title should be "{title}"')
def step_impl(context, title):
	assert_that(context.match[1]['name'], equal_to(title))

@then(u'the text should be "{text}"')
def step_impl(context, text):
	assert_that(context.match[1]['text'], equal_to(text))

@then(u'the confidence level should be greater than {confidence}')
def step_impl(context, confidence):
	assert_that(context.match[0], greater_than(float(confidence)))
