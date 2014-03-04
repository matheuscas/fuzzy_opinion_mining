import string
import nltk
import pattern.en

#stopwords from http://nlp.stanford.edu/IR-book/html/htmledition/dropping-common-terms-stop-words-1.html
STANFORD_STOPWORDS = ["a", "an", "and", "are", "as", "at","be","by","for","from",
						"has","he","in","is","it", "its","of","on","that","the",
						"to", "was","were", "will","with"]

NLTK_STOPWORDS = nltk.corpus.stopwords.words('english')

pattern_sw_file = open('stopwords-en_pattern.txt')
content = pattern_sw_file.read()
PATTERN_STOPWORDS = content.split(',')

for index in range(len(PATTERN_STOPWORDS)):
	PATTERN_STOPWORDS[index] = PATTERN_STOPWORDS[index].strip()

STOPWORDS = set(STANFORD_STOPWORDS + NLTK_STOPWORDS + PATTERN_STOPWORDS)
STOPWORDS = list(STOPWORDS)
STOPWORDS = nltk.pos_tag(STOPWORDS)

TAGS_TO_NOT_INCLUDE_IN_STOPWORDS=['JJ','JJR','JJS','RB','RBR','RBS']

STOPWORDS = [(word, tag) for word, tag in STOPWORDS if tag not in TAGS_TO_NOT_INCLUDE_IN_STOPWORDS]

UNIGRAMS = 1
BIGRAMS = 2
TRIGRAMS = 3

def stopwords_removal(text, method=None):
	"""Remove stopwords from text using the choosed method
	If method is None, the STANFORD_STOPWORDS are used to remove them.
	If method is 'nltk', the nltk lib does the stopwords removal.
	"""

	if not method:
		return __manual_stopwords_removal(text)
	elif method == "nltk":
		return __nltk_stopwords_removal(text)

def pos_tagger(tokenized_string, ngrams=None):
	"""This function does the Part of Speech tagging, using nltk lib"""

	return nltk.pos_tag(tokenized_string)

def pos_tagger_pattern(raw_text, ngrams=UNIGRAMS, continuous=False, stopwords=True):
	"""This function does the Part of Speech tagging, using pattern lib.
	It does not need the text to be tokenized first"""

	if stopwords:
		raw_text = stopwords_removal(raw_text)
	tagged = pattern.en.parse(raw_text, chunks=False)
	return pattern.en.ngrams(tagged, n=ngrams, continuous=continuous)

def extract_ngrams(doc, stopwords=True):

	doc.unigrams = pos_tagger_pattern(doc.raw_text, stopwords=stopwords)
	doc.bigrams = pos_tagger_pattern(doc.raw_text, ngrams=BIGRAMS, stopwords=stopwords)
	doc.trigrams = pos_tagger_pattern(doc.raw_text, ngrams=TRIGRAMS, stopwords=stopwords)

"""PRIVATE FUNCTIONS"""

#punctuation_removal functions
def __manual_punctuation_removal(raw_text):
	"""credits for: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python"""

	table = string.maketrans("","")
	return raw_text.translate(table, string.punctuation)

#stopwords_removal functions
def __manual_stopwords_removal(text):

	text = __manual_punctuation_removal(text)
	words = dict(STOPWORDS).keys()
	text_no_stopwords = ' '.join([w for w in text.split() if w.lower() not in words])
	return text_no_stopwords

def __nltk_stopwords_removal(text):
	"""credits for http://nltk.org/book/ch02.html"""

	text = __manual_punctuation_removal(text)
	text_no_stopwords = ' '.join([w for w in text.split() if w.lower() not in NLTK_STOPWORDS])
	return text_no_stopwords

