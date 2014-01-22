import os
import sys
import string

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import pre_processing as pp

document_sample_text = """three lengthy court cases are portrayed with spielberg's
							trademark panache - - flashy beginning , lots of facial close-ups ,
							big music , and dramatic imagery."""
document_sample_text_tokens = 26

def test_punctuation_removal():
	no_punctuation_text = pp.punctuation_removal(document_sample_text)
	for p in string.punctuation:
		assert p not in no_punctuation_text

def test_tokenizer():
	tokens = pp.tokenizer(document_sample_text)
	assert len(tokens) == document_sample_text_tokens

def test_stopwords_removal_stanford():
	no_punctuation_text = pp.punctuation_removal(document_sample_text)
	tokens = pp.tokenizer(document_sample_text)
	tokens_no_stopwords = pp.stopwords_removal(tokens)

	for t in tokens_no_stopwords:
		assert t.lower() not in pp.STANFORD_STOPWORDS

def test_stopwords_removal_nltk():
	no_punctuation_text = pp.punctuation_removal(document_sample_text)
	tokens = pp.tokenizer(document_sample_text)
	tokens_no_stopwords = pp.stopwords_removal(tokens, method='nltk')

	for t in tokens_no_stopwords:
		assert t.lower() not in pp.NLTK_STOPWORDS

def test_pos_tagger_nltk():
	no_punctuation_text = pp.punctuation_removal(document_sample_text)
	tokens = pp.tokenizer(document_sample_text)
	tokens_no_stopwords = pp.stopwords_removal(tokens, method='nltk')
	tokens_tagged = pp.pos_tagger(tokens_no_stopwords)

	for t in tokens_tagged:
		assert len(t) == 2 and t[1]