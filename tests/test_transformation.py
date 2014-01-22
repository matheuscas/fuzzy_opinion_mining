from pattern.en import wordnet
from pattern.en import NOUN, VERB, ADJECTIVE, ADVERB
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import transformation as trans

def test_word_polarity_positive():
	word_positive = "gladsome"
	synset = trans.word_polarity(word_positive)
	assert synset[0].weight[0] == 0.75 and synset[0].weight[1] == 0.75

def test_word_polarity_negative():
	word_negative = "sad"
	synset = trans.word_polarity(word_negative)
	assert synset[0].weight[0] == -0.625 and synset[0].weight[1] == 0.875
