import pre_processing as pp
import transformation as trans

class Document(object):
	"""Represent a Document"""

	def __init__(self, raw_text, original_polarity):
		self.raw_text = raw_text
		self.original_polarity = original_polarity

def create_document(file_path, original_polarity):
	return Document(open(file_path).read(), original_polarity)

def sentiment(file_path):
	raw_text = open(file_path).read()
	#pre_processing
	raw_text_no_punctuation = pp.punctuation_removal(raw_text)
	tokens = pp.tokenizer(raw_text_no_punctuation)
	tokens_no_stopwords = pp.stopwords_removal(tokens)

	#transformation
	tuples = trans.pos_tagger(tokens_no_stopwords)

	#feature selection
	tuples_JJ = [t for t in tuples if t[1] == "JJ"]

	#classification
	num_JJ = len(tuples_JJ)
	sum_JJ_polarity = 0
	for JJ in tuples_JJ:
		sum_JJ_polarity = sum_JJ_polarity + JJ[0]

	return sum_JJ_polarity / num_JJ
