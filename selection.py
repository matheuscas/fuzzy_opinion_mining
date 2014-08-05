import util

class Scenario(object):
	"""Especifies the scenario for the experiment. Negation type as 'none' means that inversion treatment will be used"""

	def __init__(self, unigrams_types=[], bigrams_types=[], trigrams_types=[], negation_type=None):
		super(Scenario, self).__init__()
		self.unigrams = unigrams_types
		self.bigrams = bigrams_types
		self.trigrams = trigrams_types
		self.negation_type = negation_type

class FeatureSelector(object):
	"""docstring for FeatureSelector"""

	def __init__(self, model, scenario):
		super(FeatureSelector, self).__init__()
		self.scenario = scenario
		self.model = model

	def __filter_adjectives_from_bigrams(self):
		filtered = False
		is_adj_unigrams = True if 'JJ' in self.scenario.unigrams else False
		for bigram_type in self.scenario.bigrams:
			if 'JJ' in bigram_type and is_adj_unigrams:
				filtered = True
				break
		return filtered

	def __filter_adjectives_from_trigrams(self):
		filtered = False
		is_adj_unigrams = True if 'JJ' in self.scenario.unigrams else False
		for trigrams_type in self.scenario.trigrams:
			if 'JJ' in trigrams_type and is_adj_unigrams:
				filtered = True
				break
		return filtered	

	def __select_unigrams(self, doc):

		doc_unigrams = []
		for unigram_type in self.scenario.unigrams:
			if unigram_type == "JJ":
				filter_adjectives_from_bigrams = self.__filter_adjectives_from_bigrams();
				filter_adjectives_from_trigrams = self.__filter_adjectives_from_trigrams();
				doc_unigrams = doc_unigrams + util.get_doc_adjectives(doc,filter_adjectives_from_bigrams, filter_adjectives_from_trigrams)
		return doc_unigrams

	def __select_bigrams(self, doc):

		doc_bigrams = []
		for bigram_type in self.scenario.bigrams:
			if bigram_type == "RB/JJ":
				bigram_items = doc['adv_adj_bigrams']
				inner_list_bigrams = []
				for bi in bigram_items:
					inner_list_bigrams.append((bi[0],bi[1]))
				doc_bigrams = doc_bigrams + inner_list_bigrams				
		return doc_bigrams			

	def select_features(self):

		ngrams = {}
		for doc in self.model.documents.find():
			doc_ngram = []
			doc_unigrams = self.__select_unigrams(doc)
			if len(doc_unigrams) > 0:
				doc_ngram = doc_ngram + doc_unigrams

			doc_bigrams = self.__select_bigrams(doc)
			if len(doc_bigrams) > 0:
				doc_ngram = doc_ngram + doc_bigrams	

			if len(doc_ngram) > 0:
				ngrams[str(doc['_id'])] = doc_ngram

		return ngrams
						
		