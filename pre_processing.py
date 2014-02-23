import string
import nltk
import pattern.en

#stopwords from http://nlp.stanford.edu/IR-book/html/htmledition/dropping-common-terms-stop-words-1.html
STANFORD_STOPWORDS = ["a", "an", "and", "are", "as", "at","be","by","for","from",
						"has","he","in","is","it", "its","of","on","that","the",
						"to", "was","were", "will","with"]

NLTK_STOPWORDS = nltk.corpus.stopwords.words('english')
UNIGRAMS = 1
BIGRAMS = 2
TRIGRAMS = 3

def tokenizer(raw_text):
	"""Split a raw_text into a list of words
	Returns a string list of words without punctuation
	"""

	return __manual_tokenizer(raw_text)

def stopwords_removal(text, method=None):
	"""Remove stopwords from text using the choosed method
	If method is None, the STANFORD_STOPWORDS are used to remove them.
	If method is 'nltk', the nltk lib does the stopwords removal.
	"""

	tokenized_string = tokenizer(text)

	if not method:
		return __manual_stopwords_removal(tokenized_string)
	elif method == "nltk":
		return __nltk_stopwords_removal(tokenized_string)

def pos_tagger(tokenized_string, ngrams=None):
	"""This function does the Part of Speech tagging, using nltk lib"""

	return nltk.pos_tag(tokenized_string)

def pos_tagger_pattern(raw_text, ngrams=UNIGRAMS, continuous=False):
	"""This function does the Part of Speech tagging, using pattern lib.
	It does not need the text to be tokenized first"""

	tagged = pattern.en.parse(raw_text, chunks=False)
	return pattern.en.ngrams(tagged, n=ngrams, continuous=continuous)

def extract_ngrams(doc):

	doc.unigrams = pos_tagger_pattern(doc.raw_text)
	doc.bigrams = pos_tagger_pattern(doc.raw_text, ngrams=BIGRAMS)
	doc.trigrams = pos_tagger_pattern(doc.raw_text, ngrams=TRIGRAMS)

"""PRIVATE FUNCTIONS"""

#punctuation_removal functions
def __manual_punctuation_removal(raw_text):
	"""credits for: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python"""

	table = string.maketrans("","")
	return raw_text.translate(table, string.punctuation)

#tokenizer functions
def __manual_tokenizer(string_text):

	no_punctuation = __manual_punctuation_removal(string_text)
	return no_punctuation.split()

#stopwords_removal functions
def __manual_stopwords_removal(tokenized_string):

	tokenized_string_no_stopwords = [w for w in tokenized_string if w.lower() not in STANFORD_STOPWORDS]
	return tokenized_string_no_stopwords

def __nltk_stopwords_removal(tokenized_string):
	"""credits for http://nltk.org/book/ch02.html"""

	content = [w for w in tokenized_string if w.lower() not in NLTK_STOPWORDS]
	return content
