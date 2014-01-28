import string
import nltk

#stopwords from http://nlp.stanford.edu/IR-book/html/htmledition/dropping-common-terms-stop-words-1.html
STANFORD_STOPWORDS = ["a", "an", "and", "are", "as", "at","be","by","for","from",
						"has","he","in","is","it", "its","of","on","that","the",
						"to", "was","were", "will","with"]

NLTK_STOPWORDS = nltk.corpus.stopwords.words('english')

def tokenizer(raw_text):
	"""Split a raw_text into a list of words"""

	return __manual_tokenizer(raw_text)

def stopwords_removal(tokenized_string, method=None):
	"""Remove stopwords from a tokenized text using the choosed method
	If method is None, the STANFORD_STOPWORDS are used to remove them.
	If method is 'nltk', the nltk lib does the stopwords removal.
	"""

	if not method:
		return __manual_stopwords_removal(tokenized_string)
	elif method == "nltk":
		return __nltk_stopwords_removal(tokenized_string)

def punctuation_removal(raw_text):
	"""Remove punctuation from raw text"""

	return __manual_punctuation_removal(raw_text)

def pos_tagger(tokenized_string):
	"""This function does the Part of Speech tagging, using nltk lib"""
	return nltk.pos_tag(tokenized_string)

"""PRIVATE FUNCTIONS"""

#punctuation_removal functions
def __manual_punctuation_removal(raw_text):
	"""credits for: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python"""

	table = string.maketrans("","")
	return raw_text.translate(table, string.punctuation)

#tokenizer functions
def __manual_tokenizer(string_text):
	return string_text.split()

#stopwords_removal functions
def __manual_stopwords_removal(tokenized_string):
	tokenized_string_no_stopwords = [w for w in tokenized_string if w.lower() not in STANFORD_STOPWORDS]
	return tokenized_string_no_stopwords

def __nltk_stopwords_removal(tokenized_string):
	"""credits for http://nltk.org/book/ch02.html"""

	content = [w for w in tokenized_string if w.lower() not in NLTK_STOPWORDS]
	return content
