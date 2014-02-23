import domain
import pre_processing as pp
import transformation as trans

class Classification(object):
	"""This class holds several classification methods"""

	NLTK_TAG_TO_SENTIWORDNET_TAG = {'JJ':'ADJECTIVE',
									'RB':'ADVERB',
									'VB':'VERB',
									'VBZ':'VERB',
									'VBP':'VERB'}

	def __init__(self, list_of_documents, extract=None):
		self.list_of_documents = list_of_documents
		self.extract = extract

	def __extract_pos_tagged_element(self, list_of_tuples, tag):
		"""extract espefics elements based on pos tag.
		list of tuples = list of (text_element, tag)"""

		return [t for t in list_of_tuples if t[1] == tag]

	def __pre_processing(self, document, extract=None):
		"""
		pre process a document with elements to extrac in extract list
		e.g.: extract = ['JJ', 'RB']
		"""

		no_punctuation = pp.punctuation_removal(document.raw_text)
		tokenized = pp.tokenizer(no_punctuation)
		no_stopwords = pp.stopwords_removal(tokenized)
		pos_tagged = pp.pos_tagger(no_stopwords)
		elements = []
		if self.extract == None:
			elements = self.__extract_pos_tagged_element(pos_tagged, "JJ")
		else:
			for e in self.extract:
				elements = elements + self.__extract_pos_tagged_element(pos_tagged, e)
		elements = set(elements)
		return elements

	def __transformation(self, elements):
		tuples = []
		for e in elements:
			weight = trans.word_polarity(e[0], Classification.NLTK_TAG_TO_SENTIWORDNET_TAG[e[1]])
			if weight:
				tuples.append(weight)
		return tuples

class OhanaBrendan(Classification):
	"""docstring for OhanaBrendan"""

	def __init__(self):
		super(OhanaBrendan, self).__init__()

	def term_counting(self):
		"""'SentiWordNet scores were calculated as positive and negative terms were
		found on each document, and used to determine sentiment orientation by
		assigning the document to the class with the highest score.'

		Based on 'Sentiment Classification of Reviews Using SentiWordNet'
		by Bruno Ohana and Brendan Tierney

		#ONLY ADJECTIVES
		positive precision = 66,26%
		negative recall = 73,20%
		accuracy = 69.56%

		#ADJECTIVES AND ADVERBS as unigrams
		positive precision = 71,37%
		negative recall = 69.30%
		accuracy = 70.32%

		#ADJECTIVES, ADVERBS AND VERBS as unigrams
		positive precision = 67,47%
		negative recall = 71.99%
		accuracy = 69.66%

		#ADJECTIVES AND VERBS as unigrams
		positive precision = 72.15%
		negative recall = 68.39%
		accuracy = 70.22%

		BEST ACCURACY: ADJECTIVES AND ADVERBS
		OVERALL ACCURACY: 69.69%
		"""

		num_of_documents = 1
		total_documents = len(self.list_of_documents)
		for d in self.list_of_documents:
			print str(num_of_documents) + '/' + str(total_documents)
			elements = self.__pre_processing(d)
			tuples = self.__transformation(elements)
			d.predicted_polarity = max(tuples, key=lambda x:abs(x[0]))[0]
			num_of_documents = num_of_documents + 1

class Custom(Classification):
	"""Custom classification methods to this research"""

	def __init__(self):
		super(Custom, self).__init__()

	def custom_classification_1(self):
		"""This classification method merges the term_counting concept from OhanaBrendan,
		but introducing the study with bigrams, trigrams and the rule-based system from
		A Sentimental Analysis of Movie Reviews Involving Fuzzy Rule- Based
		"""

		pass
