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

	def __init__(self, list_of_documents):
		self.list_of_documents = list_of_documents

	def _sentiwordnet_scores(self, elements):
		tuples = []
		for e in elements:
			word = e[0].split('/')[0]
			tag = e[0].split('/')[1]
			if len(word) > 0:
				weight = trans.word_polarity(word, Classification.NLTK_TAG_TO_SENTIWORDNET_TAG[tag])
				if weight:
					tuples.append(weight)
		return tuples

class OhanaBrendan(Classification):
	"""docstring for OhanaBrendan"""

	def _extract_pos_tagged_element(self, doc, tag):

		elements = []
		for t in doc.unigrams:
			unigram = t[0].split('/')
			if len(unigram) > 1 and unigram[1] == tag:
				elements.append(t)
		return elements
		# return [t for t in doc.unigrams if t[0].split('/')[1] == tag]

	def _select_documents(self, document, rule=None):
		"""
		pre process a document with elements to extrac in rule list
		e.g.: rule = ['JJ', 'RB']
		"""

		elements = []
		if self.rule == None:
			elements = self._extract_pos_tagged_element(document, "JJ")
		else:
			for e in self.rule:
				elements = elements + self._extract_pos_tagged_element(document, e)
		elements = set(elements)
		return elements

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
			print str(num_of_documents) + '/' + str(total_documents) + '-' + d.name
			elements = self._select_documents(d)
			tuples = self._sentiwordnet_scores(elements)
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
