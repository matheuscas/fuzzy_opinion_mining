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

def remove_sw_and_pattern_pos_tag(raw_text, ngrams=UNIGRAMS, continuous=False, stopwords=True):
	"""This function removes stopwords first and then tags the text.

	raw_text - string text from a document
	ngrams - what kind of ngram, such as UNIGRAMS, BIGRAMS or TRIGRAMS, will extracted. UNIGRAMS by default
	continuous - is pattern parameter that tells to the lib to respect or not punctuation. False by default.
	stopwords - define is stopwords will be removed or not. True by default

	return a list of tuples
	"""

	if stopwords:
		raw_text = stopwords_removal(raw_text)
	tagged = pattern.en.parse(raw_text, chunks=False)
	return pattern.en.ngrams(tagged, n=ngrams, continuous=continuous)

def pattern_pos_tag_and_remove_sw(raw_text, ngrams=UNIGRAMS, continuous=False, stopwords=True):
	"""This function does the same operations as remove_sw_and_pattern_pos_tag, except in order
	of stopwords extraction. In this function this is done after the text taggin."""

	tagged_text = pattern.en.parse(raw_text, chunks=False)
	if stopwords:
		#remove punctuation from tagged text
		penn_tags = ['CC','CD','DT','EX','FW','IN','JJ','JJR','JJS','LS','MD','NN','NNS','NNP',
					'NNPS','PDT','POS','PRP','PRP$','RB','RBR','RBS','RP','SYM','TO','UH',
					'VB','VBD','VBG','VBN','VBP','VBZ','WDT','WP','WP$','WRB']
		tagged_text_parts = tagged_text.split(' ')
		valid_parts = [part for part in tagged_text_parts if part.split('/')[1] in penn_tags]
		#remove stopwords
		words = dict(STOPWORDS).keys()
		tagged_text = ' '.join([part for part in valid_parts if part.split('/')[0] not in words])

	return pattern.en.ngrams(tagged_text, n=ngrams, continuous=continuous)

def extract_ngrams(doc, stopwords=True, rm_sw_first=True):

	if rm_sw_first:
		doc.unigrams = remove_sw_and_pattern_pos_tag(doc.raw_text, stopwords=stopwords)
		doc.bigrams = remove_sw_and_pattern_pos_tag(doc.raw_text, ngrams=BIGRAMS, stopwords=stopwords)
		doc.trigrams = remove_sw_and_pattern_pos_tag(doc.raw_text, ngrams=TRIGRAMS, stopwords=stopwords)
	else:
		doc.unigrams = pattern_pos_tag_and_remove_sw(doc.raw_text, stopwords=stopwords)
		doc.bigrams = pattern_pos_tag_and_remove_sw(doc.raw_text, ngrams=BIGRAMS, stopwords=stopwords)
		doc.trigrams = pattern_pos_tag_and_remove_sw(doc.raw_text, ngrams=TRIGRAMS, stopwords=stopwords)

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

