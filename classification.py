import domain
import pre_processing as pp
import transformation as trans
import math

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

class Pimpalkar(Classification):
	"""Class for Pimpalkar opinion mining paper"""

	ADVERBS = ['very','really','extremely','simply','always','never','not',
				'absolutely','highly','overall','truly','too']


	ADJECTIVE = 'JJ'
	ADVERB = 'RB'
	VERBS = ('VB','VBZ','VBP')
	NEGATIONS = ('not','never')

	def _sentiwordnet_scores(self, word_tag_pair_string):
		word = word_tag_pair_string.split('/')[0]
		tag = word_tag_pair_string.split('/')[1]
		if len(word) > 0:
			return trans.word_polarity(word, Classification.NLTK_TAG_TO_SENTIWORDNET_TAG[tag])
		return None

	def __fuzzy_intensity_finder(self, doc):

		case_1 = [] #RB + JJ
		case_2 = [] #(not/never) + RB/(VB/VBZ/VPB)
		case_3 = [] #(not/never) + RB/JJ
		#case_4 = [] ??? but/also/nor

		for bigram in doc.bigrams:
			bigram_1 = bigram[0]
			bigram_2 = bigram[1]
			word_tag_1 = bigram_1.split('/')
			word_tag_2 = bigram_2.split('/')
			if (word_tag_1[1] == self.ADVERB and word_tag_1[0].lower() in self.ADVERBS) and word_tag_2[1] == self.ADJECTIVE:
				case_1.append(bigram)
			elif (word_tag_1[0].lower() in self.NEGATIONS) and (word_tag_2[1] == self.ADJECTIVE or word_tag_2[1] in self.VERBS):
				case_2.append(bigram)

		for trigram in doc.trigrams:
			trigram_1 = trigram[0]
			trigram_2 = trigram[1]
			trigram_3 = trigram[2]
			word_tag_1 = trigram_1.split('/')
			word_tag_2 = trigram_2.split('/')
			word_tag_3 = trigram_3.split('/')
			if word_tag_1[0] in self.NEGATIONS and word_tag_2[0] in self.ADVERBS and word_tag_3[1] == self.ADJECTIVE:
				case_3.append(trigram)

		scores = []
		for bigram in case_1:
			jj_weight = self._sentiwordnet_scores(bigram[1])
			if jj_weight:
				if jj_weight[0] >= 0.5:
					scores.append(math.sqrt(jj_weight[0]))
				elif jj_weight[0] < 0.5:
					scores.append(math.pow(jj_weight[0],2))

		for bigram in case_2:
			rb_or_jj_weight = self._sentiwordnet_scores(bigram[1])
			if rb_or_jj_weight:
				scores.append(1 - rb_or_jj_weight[0])

		for trigram in case_3:
			jj_weight = self._sentiwordnet_scores(trigram[2])
			if jj_weight:
				A = 0
				if jj_weight[0] >= 0.5:
					A = math.sqrt(jj_weight[0])
				elif jj_weight[0] < 0.5:
					A = math.pow(jj_weight[0],2)
				B = 1 - jj_weight[0]
				scores.append(math.sqrt(A * B))

		doc.scores = scores

	def __final_sentiment_score(self, doc):
		"""It should be a summation of max polarity divided by count annotations.
		But a could'nt find out what it is that annotations"""

		doc.predicted_polarity = max(doc.scores) if len(doc.scores) > 0 else None

	def opinion_analyzer(self):

		num_of_documents = 1
		total_documents = len(self.list_of_documents)
		for doc in self.list_of_documents:
			print str(num_of_documents) + '/' + str(total_documents) + '-' + doc.name
			self.__fuzzy_intensity_finder(doc)
			self.__final_sentiment_score(doc)
			num_of_documents = num_of_documents + 1

