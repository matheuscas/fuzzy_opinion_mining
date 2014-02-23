import os
import sys
import string

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import pre_processing as pp

document_sample_text = """three lengthy court cases are portrayed with spielberg's
							trademark panache - - flashy beginning , lots of facial close-ups ,
							big music , and dramatic imagery."""
document_sample_text_tokens = 21 #without punctuation

def test_tokenizer():
	tokens = pp.tokenizer(document_sample_text)
	assert len(tokens) == document_sample_text_tokens

def test_stopwords_removal_stanford():

	tokens_no_stopwords = pp.stopwords_removal(document_sample_text)

	for t in tokens_no_stopwords:
		assert t.lower() not in pp.STANFORD_STOPWORDS

def test_stopwords_removal_nltk():

	tokens_no_stopwords = pp.stopwords_removal(document_sample_text, method='nltk')

	for t in tokens_no_stopwords:
		assert t.lower() not in pp.NLTK_STOPWORDS

def test_pos_tagger_nltk():

	tokens_no_stopwords = pp.stopwords_removal(document_sample_text, method='nltk')
	tokens_tagged = pp.pos_tagger(tokens_no_stopwords)

	for t in tokens_tagged:
		assert len(t) == 2 and t[1]


