from pattern.en import wordnet
from pattern.en import NOUN, VERB, ADJECTIVE, ADVERB
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import transformation as trans

def test_word_polarity_positive():
	word_positive = "gladsome"
	weight = trans.word_polarity(word_positive)
	assert weight[0] == 0.75 and weight[1] == 0.75

def test_word_polarity_negative():
	word_negative = "sad"
	weight = trans.word_polarity(word_negative)
	assert weight[0] == -0.625 and weight[1] == 0.875

def test_word_not_found():
	word_negative = "man"
	weight = trans.word_polarity(word_negative)
	assert weight == None
