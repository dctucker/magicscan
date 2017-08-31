Feature: convert image to text
	In order to organize my collection
	As a collector of cards
	I want to identify cards using a camera

	Scenario: Title and text are recognized
		Given an image "2crop.jpg"
		When the image is scanned
		Then the title should be "AWOL"
		And the text should be "Remove target attacking creature from the game. Then remove it from the removed-from-game zone and put it into the absolutely-removed-from-the-freaking-game-forever zone."
		And the confidence level should be greater than 0.7

	Scenario: Only text is recognized
		Given an image "2crop.jpg"
		When the image is scanned
		Then the title should be "AWOL"
		And the text should be "Remove target attacking creature from the game. Then remove it from the removed-from-game zone and put it into the absolutely-removed-from-the-freaking-game-forever zone."
		And the confidence level should be greater than 0.5
