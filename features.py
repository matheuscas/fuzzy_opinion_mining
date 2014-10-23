import pymongo
import transformation
import util
import lexicons
import plotly.plotly as py
import numpy as np
import arff
from textblob import blob, TextBlob, Word
from textblob.taggers import PatternTagger
from textblob.wordnet import ADV, ADJ, NOUN, VERB
from collections import Counter
from bson.code import Code
from plotly.graph_objs import *

class ModelFeatures(object):
	"""docstring for ModelFeatures"""
	def __init__(self, model):
		super(ModelFeatures, self).__init__()
		self.model = model
		self.features = {}
		self.positives_features = {}
		self.negatives_features = {}
		self.MAPPER = Code("""
               function () {
                 this.adjectives.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)
		self.documents_stats = []
		self.BINARY_POSITIVE_POLARITY = 1
		self.BINARY_NEGATIVE_POLARITY = 0
		self.MULTIPLE_POSITIVE_POLARITY = 4
		self.MULTIPLE_NEGATIVE_POLARITY = 2
		self.prior_polarity_score = False
		self.trim_polarity = False
		self.positive_limit = 0.875
		self.negative_limit = -0.25
		self.binary_degree = True
		self.plotly_login = None
		self.plotly_password = None

	def __documents_stats(self):

		if len(self.documents_stats) > 0:
			return self.documents_stats

		list_of_doc_stats = []
		temp_num = 1
		for doc in self.model.documents.find():
			doc_stats = {}
			print temp_num
			ngrams = util.get_doc_ngrams(doc,bigrams_types=['ADV/ADJ'], use_trigrams=False, filtered=True)
			positive_ngrams = []
			negative_ngrams = []
			for ngram in ngrams:
				ngram_pol = transformation.ngrams_polarities([ngram], prior_polarity_score=self.prior_polarity_score)
				if ngram_pol is None or len(ngram_pol) == 0:
					ngram_pol = (0,0)
				if ngram_pol[0] > 0:
					positive_ngrams.append(ngram)
				elif ngram_pol[0] < 0:
					negative_ngrams.append(ngram)		
			doc_stats['positive_ngrams'] = positive_ngrams
			doc_stats['negative_ngrams'] = negative_ngrams
			doc_stats['_id'] = str(doc['_id'])

			positive_verbs = []
			negative_verbs = [] 

			for verb in doc['verbs']:
				verb_pol = transformation.word_polarity(verb, pos_tag="VERB", prior_polarity_score=True)
				if verb_pol is None or len(verb_pol) == 0:
					verb_pol = (0,0)
				if verb_pol[0] > 0:
					positive_verbs.append(verb)
				elif verb_pol[0] < 0:
					negative_verbs.append(verb)
			doc_stats['positive_verbs'] = positive_verbs
			doc_stats['negative_verbs'] = negative_verbs			
			list_of_doc_stats.append(doc_stats)
			temp_num = temp_num + 1

		self.documents_stats = list_of_doc_stats 	
		return list_of_doc_stats

	def __set_doc_type(self, doc_pol, key_sufix, binary_degree=True):

		polarity = self.BINARY_POSITIVE_POLARITY if binary_degree else self.MULTIPLE_POSITIVE_POLARITY
		key_prefix = "positive_"
		if doc_pol == 'negatives':
			polarity = self.BINARY_NEGATIVE_POLARITY if binary_degree else self.MULTIPLE_NEGATIVE_POLARITY
			key_prefix = "negative_"

		key_name = key_prefix + key_sufix
		return (polarity, key_name)

	def __set_polarity_test(self, binary_degree, doc, polarity, doc_type):

		if binary_degree:
				test_pol = doc['polarity'] == polarity
		else:
			if doc_type == 'positives':
				test_pol = int(doc['degree']) >= polarity
			elif doc_type == 'negatives':
				test_pol = int(doc['degree']) <= polarity

		return test_pol

	def _trim_ngram_list(self, ngram_list):
		
		trimmed_ngram_polarities = []
		ngram_polarities = transformation.ngrams_polarities(ngram_list, prior_polarity_score=self.prior_polarity_score)
		for pol in ngram_polarities:
			if (pol > 0 and pol >= self.positive_limit) or (pol < 0 and pol <= self.negative_limit):
				trimmed_ngram_polarities.append(pol)
		return trimmed_ngram_polarities		

	def most_frequent_negative_ngrams(self):
		
		if 'most_frequent_negative_ngrams' in self.features.keys():
			return self.features['most_frequent_negative_ngrams']

		results = self.model.documents.map_reduce(self.MAPPER, self.model.REDUCER, 'tempresults')
		sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
		self.model.database['tempresults'].drop()
		most_frequent_negative_ngrams = []
		for x in sorted_results:
			polarity = transformation.word_polarity(x['_id'], prior_polarity_score=self.prior_polarity_score)
			if polarity is not None and polarity[0] < 0:
				most_frequent_negative_ngrams.append(x)

		self.features['most_frequent_negative_ngrams'] = most_frequent_negative_ngrams		
		return most_frequent_negative_ngrams

	def most_frequent_positive_ngrams(self):
		
		if 'most_frequent_positive_ngrams' in self.features.keys():
			return self.features['most_frequent_positive_ngrams']

		results = self.model.documents.map_reduce(self.MAPPER, self.model.REDUCER, 'tempresults')
		sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
		self.model.database['tempresults'].drop()
		most_frequent_positive_ngrams = []
		for x in sorted_results:
			polarity = transformation.word_polarity(x['_id'], prior_polarity_score=self.prior_polarity_score)
			if polarity is not None and polarity[0] > 0:
				most_frequent_positive_ngrams.append(x)

		self.features['most_frequent_positive_ngrams'] = most_frequent_positive_ngrams		
		return most_frequent_positive_ngrams

	def most_frequent_polar_adjectives_in_polar_documents(self, adjectives_polarity='positives',docs_polarity='positives'):
		
		key_name = 'most_frequent_' + adjectives_polarity + '_adjectives_in_' + docs_polarity + '_documents'
		if key_name in self.features.keys():
			return self.features[key_name]

		all_polar_adjectives = []
		polarity, key = self.__set_doc_type(docs_polarity, key_name, self.binary_degree) #key is not used. Refactor later #TODO
		key = 'positive_ngrams' if adjectives_polarity == 'positives' else 'negative_ngrams' #Key, here, is overriden
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				all_polar_adjectives = all_polar_adjectives + stat[key]
		all_polar_adjectives_freq = Counter(all_polar_adjectives)
		self.features[key_name] = all_polar_adjectives_freq
		return all_polar_adjectives_freq
			
	def general(self):

		if 'general' in self.features.keys():
			return self.features['general']

		num_of_docs = self.model.documents.count()
		sentences_per_doc = []
		adjectives_per_doc = []
		adverbs_per_doc = []
		adv_adj_bigram_per_doc = []
		for ndoc in self.model.documents.find():
			sentences_per_doc.append(len(TextBlob(ndoc['text']).sentences))
			adjectives_per_doc.append(len(ndoc['adjectives']))
			adv_adj_bigram_per_doc.append(len(ndoc['adv_adj_bigrams']))
			try:
				adverbs_per_doc.append(len(ndoc['adverbs']))	
			except Exception, e:
				pass

		if len(sentences_per_doc) > 0:
			sentences_avg = util.average(sentences_per_doc)
			sentences_std = util.std(sentences_per_doc)
		else:
			sentences_avg = 0
			sentences_std = 0	

		if len(adjectives_per_doc) > 0:	
			adjectives_avg = util.average(adjectives_per_doc)
			adjectives_std = util.std(adjectives_per_doc)
		else:
			adjectives_avg = 0
			adjectives_std = 0

		if len(adverbs_per_doc) > 0:
			adverbs_avg = util.average(adverbs_per_doc)
			adverbs_std = util.std(adverbs_per_doc)
		else:
			adverbs_avg = 0
			adverbs_std = 0

		if len(adv_adj_bigram_per_doc) > 0:	
			adv_adj_bigram_avg = util.average(adv_adj_bigram_per_doc)
			adv_adj_bigram_std = util.std(adv_adj_bigram_per_doc)
		else:
			adv_adj_bigram_avg = 0
			adv_adj_bigram_std = 0	
		
		general = {"avg of sentences":sentences_avg, "sentences std": sentences_std, 
								"avg of adjectives": adjectives_avg, "adjectives std":adjectives_std,
								"avg of adverbs": adverbs_avg, "adverbs std": adverbs_std,
								"RB/JJ bigram avg":adv_adj_bigram_avg,"RB/JJ bigram std":adv_adj_bigram_std}
		self.features['general'] = general						
		return general						
				
	def documents_highest_count_positive_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_count_positive_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_num_pos_adj = 0.0
		docs_highest_num_pos_adj = []
		num_of_docs = 0.0
		highest_count_distribution = []
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				num_pos_adj = len(self._trim_ngram_list(stat['positive_ngrams']))
				num_neg_adj = len(self._trim_ngram_list(stat['negative_ngrams']))
			else:
				num_pos_adj = len(stat['positive_ngrams'])
				num_neg_adj = len(stat['negative_ngrams'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if num_pos_adj > num_neg_adj:
					amount_docs_highest_num_pos_adj += 1
					docs_highest_num_pos_adj.append(str(doc['_id']))
					highest_count_distribution.append(len(stat['positive_ngrams']))

		print num_of_docs			
		self.features[key_name] = (amount_docs_highest_num_pos_adj / num_of_docs, amount_docs_highest_num_pos_adj, docs_highest_num_pos_adj, highest_count_distribution)
		
		return self.features[key_name]	

	def documents_highest_count_negative_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_count_negative_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_count_neg_adj = 0.0
		docs_highest_num_neg_adj = []
		num_of_docs = 0.0
		highest_count_distribution = []
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				num_pos_adj = len(self._trim_ngram_list(stat['positive_ngrams']))
				num_neg_adj = len(self._trim_ngram_list(stat['negative_ngrams']))
			else:
				num_pos_adj = len(stat['positive_ngrams'])
				num_neg_adj = len(stat['negative_ngrams'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if num_pos_adj < num_neg_adj:
					amount_docs_highest_count_neg_adj += 1
					docs_highest_num_neg_adj.append(str(doc['_id']))
					highest_count_distribution.append(len(stat['negative_ngrams']))

		self.features[key_name] = (amount_docs_highest_count_neg_adj / num_of_docs, amount_docs_highest_count_neg_adj, docs_highest_num_neg_adj, highest_count_distribution)
		
		return self.features[key_name]

	def documents_equal_count_positive_and_negative_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_count_positive_and_negative_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_count_adj = 0.0
		docs_equal_num_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				num_pos_adj = len(self._trim_ngram_list(stat['positive_ngrams']))
				num_neg_adj = len(self._trim_ngram_list(stat['negative_ngrams']))
			else:
				num_pos_adj = len(stat['positive_ngrams'])
				num_neg_adj = len(stat['negative_ngrams'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if num_pos_adj == num_neg_adj:
					amount_docs_equal_count_adj += 1
					docs_equal_num_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_equal_count_adj / num_of_docs, amount_docs_equal_count_adj, docs_equal_num_adj)
		
		return self.features[key_name]

	def create_histogram(self, dist_list, hist_file_name, hist_title, traces_name, xaxis_title='', yaxis_title='',bins=None):
		
		if self.plotly_login is None or self.plotly_password is None:
			raise Exception('Plotly credentials not configured')

		py.sign_in(self.plotly_login, self.plotly_password)
		traces = []
		if len(dist_list) == 1:
			if bins:
				traces.append(Histogram(
					x=dist_list[0], 
					xbins=XBins(
						start=bins[0],
						end=bins[1],
						size=bins[2]
					),
					name=traces_name[0]
				))
			else:
				traces.append(Histogram(x=dist_list[0],name=traces_name[0]))
		elif len(dist_list) > 1:
			for idx, dist in enumerate(dist_list):
				if bins:
					traces.append(Histogram(
						x=dist, 
						xbins=XBins(
							start=bins[0],
							end=bins[1],
							size=bins[2]
						), 
						opacity=0.75,
						name=traces_name[idx]
					))
				else:
					traces.append(Histogram(
						x=dist, 
						opacity=0.75, 
						name=traces_name[idx]
					))

		data = Data(traces)
		layout = Layout(
		    barmode='overlay',
		    title=hist_title,
		    xaxis=XAxis(
        		title=xaxis_title
        	),
        	yaxis=YAxis(
        		title=yaxis_title
        	)	
		)
		fig = Figure(data=data, layout=layout)
		plot_url = py.plot(fig, filename=hist_file_name)		

	def get_dist_highest_count_positive_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO	
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				dist.append(len(doc_stat['positive_ngrams']))

		return np.array(dist)

	def get_dist_highest_count_negative_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				dist.append(len(doc_stat['negative_ngrams']))

		return np.array(dist)

	def documents_highest_sum_positive_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_sum_positive_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_sum_pos_adj = 0.0
		docs_highest_sum_pos_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				sum_pos_adj = abs(sum(self._trim_ngram_list(stat['positive_ngrams'])))
				sum_neg_adj = abs(sum(self._trim_ngram_list(stat['negative_ngrams'])))
			else:	
				sum_pos_adj = abs(sum(transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)))
				sum_neg_adj = abs(sum(transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj > sum_neg_adj:
					amount_docs_highest_sum_pos_adj += 1
					docs_highest_sum_pos_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_highest_sum_pos_adj / num_of_docs, amount_docs_highest_sum_pos_adj, docs_highest_sum_pos_adj)

		return self.features[key_name]			

	def documents_highest_sum_negative_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_sum_negative_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_sum_neg_adj = 0.0
		docs_highest_sum_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				sum_pos_adj = abs(sum(self._trim_ngram_list(stat['positive_ngrams'])))
				sum_neg_adj = abs(sum(self._trim_ngram_list(stat['negative_ngrams'])))
			else:	
				sum_pos_adj = abs(sum(transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)))
				sum_neg_adj = abs(sum(transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj < sum_neg_adj:
					amount_docs_highest_sum_neg_adj += 1
					docs_highest_sum_neg_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_highest_sum_neg_adj / num_of_docs, amount_docs_highest_sum_neg_adj, docs_highest_sum_neg_adj)

		return self.features[key_name]
		
	def documents_equal_sum_positive_and_negative_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_sum_positive_and_negative_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_sum_pos_neg_adj = 0.0
		docs_equal_sum_pos_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				sum_pos_adj = abs(sum(self._trim_ngram_list(stat['positive_ngrams'])))
				sum_neg_adj = abs(sum(self._trim_ngram_list(stat['negative_ngrams'])))
			else:	
				sum_pos_adj = abs(sum(transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)))
				sum_neg_adj = abs(sum(transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj == sum_neg_adj:
					amount_docs_equal_sum_pos_neg_adj += 1
					docs_equal_sum_pos_neg_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_equal_sum_pos_neg_adj / num_of_docs, amount_docs_equal_sum_pos_neg_adj, docs_equal_sum_pos_neg_adj)

		return self.features[key_name]	

	def get_dist_highest_sum_positive_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				dist.append(sum(transformation.ngrams_polarities(doc_stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)))

		return np.array(dist)

	def get_dist_highest_sum_negative_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				dist.append(sum(transformation.ngrams_polarities(doc_stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)))

		return np.array(dist)

	def documents_highest_score_positive_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_score_positive_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_score_pos_adj = 0.0
		docs_highest_score_pos_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				pos_ngrams = self._trim_ngram_list(stat['positive_ngrams'])
				neg_ngrams = self._trim_ngram_list(stat['negative_ngrams'])
			else:	
				pos_ngrams = transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
				neg_ngrams = transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_ngrams) == 0 else util.max_abs(pos_ngrams)
			max_neg_adj = 0 if len(neg_ngrams) == 0 else util.max_abs(neg_ngrams)

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if abs(max_pos_adj) > abs(max_neg_adj):
					amount_docs_highest_score_pos_adj += 1
					docs_highest_score_pos_adj.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_highest_score_pos_adj / num_of_docs, amount_docs_highest_score_pos_adj, docs_highest_score_pos_adj)

		return self.features[key_name]			

	def documents_highest_score_negative_ngrams(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_score_negative_ngrams', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_score_neg_adj = 0.0
		docs_highest_score_neg_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				pos_ngrams = self._trim_ngram_list(stat['positive_ngrams'])
				neg_ngrams = self._trim_ngram_list(stat['negative_ngrams'])
			else:	
				pos_ngrams = transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
				neg_ngrams = transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_ngrams) == 0 else util.max_abs(pos_ngrams)
			max_neg_adj = 0 if len(neg_ngrams) == 0 else util.max_abs(neg_ngrams)

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if abs(max_pos_adj) < abs(max_neg_adj):
					amount_docs_highest_score_neg_adj += 1
					docs_highest_score_neg_adj.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_highest_score_neg_adj / num_of_docs, amount_docs_highest_score_neg_adj, docs_highest_score_neg_adj)

		return self.features[key_name]

	def documents_equal_score_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_score_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_adj_score = 0.0
		docs_equal_adj_scores = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if self.trim_polarity:
				pos_ngrams = self._trim_ngram_list(stat['positive_ngrams'])
				neg_ngrams = self._trim_ngram_list(stat['negative_ngrams'])
			else:	
				pos_ngrams = transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
				neg_ngrams = transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_ngrams) == 0 else util.max_abs(pos_ngrams)
			max_neg_adj = 0 if len(neg_ngrams) == 0 else util.max_abs(neg_ngrams)

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if abs(max_pos_adj) == abs(max_neg_adj):
					amount_docs_equal_adj_score += 1
					docs_equal_adj_scores.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_equal_adj_score / num_of_docs, amount_docs_equal_adj_score, docs_equal_adj_scores)

		return self.features[key_name]

	def get_dist_highest_score_positive_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:	
				pos_ngrams = transformation.ngrams_polarities(doc_stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
				max_pos_adj = 0 if len(pos_ngrams) == 0 else util.max_abs(pos_ngrams)
				dist.append(max_pos_adj)

		return np.array(dist)

	def get_dist_highest_score_negative_ngrams(self, docs_polarity='all'):

		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		dist = []	
		for doc_stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(doc_stat['_id'])
			if docs_polarity == 'all':
				test_polarity = True
			else:
				test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				neg_ngrams = transformation.ngrams_polarities(doc_stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
				max_neg_adj = 0 if len(neg_ngrams) == 0 else util.max_abs(neg_ngrams)
				dist.append(max_neg_adj)

		return np.array(dist)

	def get_dist_positive_polarities(self, docs_polarity='positives'):

		all_polar_adjectives = []
		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				all_polar_adjectives = all_polar_adjectives + transformation.ngrams_polarities(stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
		return all_polar_adjectives

	def get_dist_negative_polarities(self, docs_polarity='positives'):
		
		all_polar_adjectives = []
		polarity, key = self.__set_doc_type(docs_polarity, '', self.binary_degree) #key is not used. Refactor later #TODO
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			test_polarity = self.__set_polarity_test(self.binary_degree, doc, polarity, docs_polarity)
			if test_polarity:
				all_polar_adjectives = all_polar_adjectives + transformation.ngrams_polarities(stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
		return all_polar_adjectives

	def get_arff_file(self, normalize=False):
		
		relation = self.model.database.name + '_features'
		dataset_features = {
			'description': self.model.database.name + ' dataset',
			'relation': relation,
			'attributes':[
				('id','STRING'),
				('polarity',['positive','negative']),
				('positive_term_count','INTEGER'),
				('negative_term_count','INTEGER'),
				('ngrams_positive_sum','REAL'),
				('ngrams_negative_sum','REAL'),
				('ngrams_positive_highest_score','REAL'),
				('ngrams_negative_highest_score','REAL'),
				('document_size','INTEGER'),
				('ngrams_size','INTEGER'),
				('verbs_positive_sum','REAL'),
				('verbs_negative_sum','REAL'),
				('ngrams_sum_pos_to_neg_ratio','REAL'),
				('verbs_sum_pos_to_neg_ratio','REAL'),
				('ngrams_count_pos_to_neg_ratio','REAL'),
				('ngrams_score_pos_to_neg_ratio','REAL'),
			]	
		}
		
		data = [] #it should be a list of lists.
		tagger = util.get_tagger()
		for doc_stat in self.__documents_stats():

			doc = self.model.get_doc_by_id(doc_stat['_id'])
			doc_blob = tagger(doc['text'])
			polarity = 'positive' if util.is_doc_positive(doc) else 'negative'

			positive_term_count = len(doc_stat['positive_ngrams'])
			negative_term_count = len(doc_stat['negative_ngrams'])
			ngrams_count_pos_to_neg_ratio = 0
			if negative_term_count > 0:
				ngrams_count_pos_to_neg_ratio = float(positive_term_count) / float(negative_term_count)

			doc_size = len(doc_blob.words)
			ngrams_qtd = negative_term_count + positive_term_count

			ngrams_pos_sum = sum(transformation.ngrams_polarities(doc_stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score))
			ngrams_neg_sum = sum(transformation.ngrams_polarities(doc_stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score))

			pos_ngrams = transformation.ngrams_polarities(doc_stat['positive_ngrams'], prior_polarity_score=self.prior_polarity_score)
			neg_ngrams = transformation.ngrams_polarities(doc_stat['negative_ngrams'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_ngrams) == 0 else util.max_abs(pos_ngrams)
			max_neg_adj = 0 if len(neg_ngrams) == 0 else util.max_abs(neg_ngrams)

			ngrams_score_pos_to_neg_ratio = 0
			if abs(max_neg_adj) > 0:
				ngrams_score_pos_to_neg_ratio = max_pos_adj / abs(max_neg_adj)

			verbs_positive_sum = []
			for vp in doc_stat['positive_verbs']:
				vpp = transformation.word_polarity(vp, pos_tag="VERB", prior_polarity_score=True)
				if vpp is not None and vpp[0] != 0:
					verbs_positive_sum.append(vpp[0])

			ngrams_qtd = ngrams_qtd + len(verbs_positive_sum)
			verbs_positive_sum = sum(verbs_positive_sum);		

			verbs_negative_sum = []
			for vn in doc_stat['negative_verbs']:
				vnp = transformation.word_polarity(vn, pos_tag="VERB", prior_polarity_score=True)
				if vnp is not None and vnp[0] != 0:
					verbs_negative_sum.append(vnp[0])

			ngrams_qtd = ngrams_qtd + len(verbs_negative_sum)		
			verbs_negative_sum = sum(verbs_negative_sum);

			verbs_sum_pos_to_neg_ratio = 0
			if abs(verbs_negative_sum) > 0:
				verbs_sum_pos_to_neg_ratio = verbs_positive_sum / abs(verbs_negative_sum)

			features = [doc_stat['_id'],
						polarity, 
						positive_term_count, 
						negative_term_count, 
						ngrams_pos_sum, 
						ngrams_neg_sum, 
						max_pos_adj, 
						max_neg_adj, 
						doc_size, 
						ngrams_qtd,
						verbs_positive_sum,
						verbs_negative_sum,
						ngrams_sum_pos_to_neg_ratio,
						verbs_sum_pos_to_neg_ratio,
						ngrams_count_pos_to_neg_ratio,
						ngrams_score_pos_to_neg_ratio]

			if normalize:
				positive_term_count_by_doc_size = positive_term_count / float(doc_size)
				negative_term_count_by_doc_size = negative_term_count / float(doc_size)
				ngrams_pos_sum_by_doc_size = ngrams_pos_sum / float(doc_size)
				ngrams_neg_sum_by_doc_size = ngrams_neg_sum / float(doc_size)
				verbs_positive_sum_by_doc_size = verbs_positive_sum / float(doc_size)
				verbs_negative_sum_by_doc_size = verbs_negative_sum / float(doc_size)

				if ngrams_qtd > 0:
					positive_term_count_by_ngrams = positive_term_count / float(ngrams_qtd)
					negative_term_count_by_ngrams = negative_term_count / float(ngrams_qtd)
					ngrams_pos_sum_by_ngrams = ngrams_pos_sum / float(ngrams_qtd)
					ngrams_neg_sum_by_ngrams = ngrams_neg_sum / float(ngrams_qtd)
					verbs_positive_sum_by_ngrams = verbs_positive_sum / float(ngrams_qtd)
					verbs_negative_sum_by_ngrams = verbs_negative_sum / float(ngrams_qtd)
				else:
					positive_term_count_by_ngrams = 0.0
					negative_term_count_by_ngrams = 0.0
					ngrams_pos_sum_by_ngrams = 0.0
					ngrams_neg_sum_by_ngrams = 0.0
					verbs_positive_sum_by_ngrams = 0.0
					verbs_negative_sum_by_ngrams = 0.0
				
				features = features + [positive_term_count_by_doc_size, 
										negative_term_count_by_doc_size, 
										ngrams_pos_sum_by_doc_size, 
										ngrams_neg_sum_by_doc_size,
										positive_term_count_by_ngrams, 
										negative_term_count_by_ngrams, 
										ngrams_pos_sum_by_ngrams, 
										ngrams_neg_sum_by_ngrams,
										verbs_positive_sum_by_doc_size,
										verbs_negative_sum_by_doc_size,
										verbs_positive_sum_by_ngrams,
										verbs_negative_sum_by_ngrams]
			data.append(features)

		file_name = self.model.database.name
		if normalize:
			file_name = file_name + '_normalize'
			dataset_features['attributes'] = dataset_features['attributes'] + \
											[('positive_term_count_by_doc_size','REAL'),
											('negative_term_count_by_doc_size','REAL'),
											('ngrams_positive_sum_by_doc_size','REAL'),
											('ngrams_negative_sum_by_doc_size','REAL'),
											('positive_term_count_by_ngrams','REAL'),
											('negative_term_count_by_ngrams','REAL'),
											('ngrams_positive_sum_by_ngrams','REAL'),
											('ngrams_negative_sum_by_ngrams','REAL'),
											('verbs_positive_sum_by_doc_size','REAL'),
											('verbs_negative_sum_by_doc_size','REAL'),
											('verbs_positive_sum_by_ngrams','REAL'),
											('verbs_negative_sum_by_ngrams','REAL')]


		file_name = file_name  + '.arff'
		dataset_features['data'] = data	
		arff_str = arff.dumps(dataset_features)
		f = open(file_name,'w+')
		f.write(arff_str)


class SubjectivityClues(ModelFeatures):
	"""Features for SubjectivityClues"""

	def __init__(self, model):
		ModelFeatures.__init__(self, model)
		self.lexicon = lexicons.SubjectivityClues()
		self.lexicon_cache = {}

	def __load_lexicon_to_cache(self):
		for e in self.lexicon.entries.find(timeout=False):
			self.lexicon_cache[e['word1']] = e

	def __get_docs_subjectivity_clues(self, doc):
		tagger = util.get_tagger()
		blob_text = tagger(doc['text'])
		blob_word = None
		clues = []
		self.__load_lexicon_to_cache()
		for word, tag in util.tags(blob_text):
			wordnet_tag = blob._penn_to_wordnet(tag)
			word_lemma = Word(word).lemmatize(wordnet_tag)	

			if word in self.lexicon_cache:
				clues.append(self.lexicon_cache[word])
			elif word_lemma in self.lexicon_cache:
				clues.append(self.lexicon_cache[word_lemma])
		return clues
		
	def __get_weak_subjectivity_clues(self, doc_subjectivity_clues):
		weak_scs = []
		for sc in doc_subjectivity_clues:
			if sc['type'] == 'weaksubj':
				weak_scs.append(sc)
		return weak_scs

	def __get_positive_weak_subjectivity_clues(self, doc_weak_subjectivity_clues):
		pos_weak_scs = []
		for sc in doc_weak_subjectivity_clues:
			if sc['priorpolarity'] == 'positive':
				pos_weak_scs.append(sc)
		return pos_weak_scs	

	def __get_negative_weak_subjectivity_clues(self, doc_weak_subjectivity_clues):
		neg_weak_scs = []
		for sc in doc_weak_subjectivity_clues:
			if sc['priorpolarity'] == 'negative':
				neg_weak_scs.append(sc)
		return neg_weak_scs

	def __get_strong_subjectivity_clues(self, doc_subjectivity_clues):
		strong_scs = []
		for sc in doc_subjectivity_clues:
			if sc['type'] == 'strongsubj':
				strong_scs.append(sc)
		return strong_scs
		
	def __get_positive_strong_subjectivity_clues(self, doc_strong_subjectivity_clues):
		pos_strong_scs = []
		for sc in doc_strong_subjectivity_clues:
			if sc['priorpolarity'] == 'positive':
				pos_strong_scs.append(sc)
		return pos_strong_scs
		
	def __get_negative_strong_subjectivity_clues(self, doc_strong_subjectivity_clues):
		neg_strong_scs = []
		for sc in doc_strong_subjectivity_clues:
			if sc['priorpolarity'] == 'negative':
				neg_strong_scs.append(sc)
		return neg_strong_scs					

	def documents_with_subjectivity_clues(self, doc_type, binary_degree=True):
		
		polarity, key_name = self._ModelFeatures__set_doc_type(doc_type, 'documents_with_subjectivity_clues', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		scs_in_docs = []
		weak_scs_in_docs = []
		pos_weak_scs_in_docs = []
		neg_weak_scs_in_docs = []
		strong_scs_in_docs = []
		pos_strong_scs_in_docs = []
		neg_strong_scs_in_docs = []

		docs_qtd = 0.0
		for doc in self.model.documents.find(timeout=False):
			test_pol = self._ModelFeatures__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				docs_sc = self.__get_docs_subjectivity_clues(doc)
				scs_in_docs.append(len(docs_sc))

				docs_weak_sc = self.__get_weak_subjectivity_clues(docs_sc)
				weak_scs_in_docs.append(len(docs_weak_sc))

				docs_pos_weak_sc = self.__get_positive_weak_subjectivity_clues(docs_weak_sc)
				pos_weak_scs_in_docs.append(len(docs_pos_weak_sc))

				docs_neg_weak_sc = self.__get_negative_weak_subjectivity_clues(docs_weak_sc)
				neg_weak_scs_in_docs.append(len(docs_neg_weak_sc))

				docs_strong_sc = self.__get_strong_subjectivity_clues(docs_sc)
				strong_scs_in_docs.append(len(docs_strong_sc))

				docs_pos_strong_sc = self.__get_positive_strong_subjectivity_clues(docs_strong_sc)
				pos_strong_scs_in_docs.append(len(docs_pos_strong_sc))

				docs_neg_strong_sc = self.__get_negative_strong_subjectivity_clues(docs_strong_sc)
				neg_strong_scs_in_docs.append(len(docs_neg_strong_sc))

				docs_qtd += 1.0
				print docs_qtd

		sc_avg = util.average(scs_in_docs)
		sc_std = util.std(scs_in_docs)
		general_stats = (sc_avg, sc_std, docs_qtd)

		weak_sc_avg = util.average(weak_scs_in_docs)
		weak_sc_std = util.std(weak_scs_in_docs)
		pos_weak_sc_avg = util.average(pos_weak_scs_in_docs)
		pos_weak_sc_std = util.std(pos_weak_scs_in_docs)
		neg_weak_sc_avg = util.average(neg_weak_scs_in_docs)
		neg_weak_sc_std = util.std(neg_weak_scs_in_docs)
		weak_stats = (weak_sc_avg, weak_sc_std, pos_weak_sc_avg, pos_weak_sc_std, neg_weak_sc_avg, neg_weak_sc_std)

		strong_sc_avg = util.average(strong_scs_in_docs)
		strong_sc_std = util.std(strong_scs_in_docs)
		pos_strong_sc_avg = util.average(pos_strong_scs_in_docs)
		pos_strong_sc_std = util.std(pos_strong_scs_in_docs)
		neg_strong_sc_avg = util.average(neg_strong_scs_in_docs)
		neg_strong_sc_std = util.std(neg_strong_scs_in_docs)
		strong_stats = (strong_sc_avg, strong_sc_std, pos_strong_sc_avg, pos_strong_sc_std, neg_strong_sc_avg, neg_strong_sc_std)

		return general_stats, weak_stats, strong_stats		

class NgramsDistribuition(ModelFeatures):
	"""docstring for NgramsDistribuition"""
	
	def __init__(self, model):
		ModelFeatures.__init__(self, model)
		self.ngrams_distribuition = []

	def create_basic_model(self):
		"""Creates a list of dict elements with the following format:
			{'id':doc id,'polarity':polarity or degree ,'first_sentences':list of sentences, 'last_sentences':list of sentences}
		"""
		
		self.ngrams_distribuition = []
		tagger = util.get_tagger()
		aux_count = self.model.documents.count()
		aux_qtd = 1 
		for doc in self.model.documents.find(timeout=False):
			print 'create_basic_model', aux_qtd, aux_count
			_id = str(doc['_id'])
			_polarity = doc['polarity'] if 'polarity' in doc else doc['degree']
			first_sentences = []
			second_sentences = []
			doc_blob = tagger(doc['text'])
			num_of_sentences = len(doc_blob.sentences)
			if num_of_sentences == 1:
				split_index = len(doc_blob.words) / 2
				sentence_tags = doc_blob.tags
				first_sentences = sentence_tags[0:split_index]
				second_sentences = sentence_tags[split_index:]
			else:
				split_index = num_of_sentences / 2
				first_sentences = doc_blob.sentences[0:split_index]
				second_sentences = doc_blob.sentences[split_index:]
			self.ngrams_distribuition.append({'id':_id,'polarity':_polarity,'num_of_sentences': num_of_sentences,'first_sentences':first_sentences,'last_sentences':second_sentences})
			aux_qtd += 1

		self.__store_model_to_db()	

	def __blob_sentence_to_dict_list(self, list_of_blob_sentences):

		sentences_objs = list_of_blob_sentences
		sentences_dics = []
		for s in sentences_objs:
			if type(s) is not tuple:
				sentences_dics.append(s.dict)
			else:
				sentences_dics.append(s)
		return sentences_dics

	def __dict_to_blob_sentence(self, _dict):

		blob_sentence = blob.Sentence(_dict['raw'])
		blob_sentence.start_index = _dict['start_index']
		blob_sentence.end_index = _dict['end_index']
		blob_sentence.stripped = _dict['stripped']
		blob_sentence.noun_phrases = _dict['noun_phrases']
		blob_sentence.polarity = _dict['polarity']
		blob_sentence.subjectivity = _dict['subjectivity']
		return blob_sentence

	def __store_model_to_db(self):

		self.model.database['ngrams_distribuition'].drop()
		collection = self.model.database['ngrams_distribuition']
		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1 
		for nd in self.ngrams_distribuition:
			print 'store_model_to_db', aux_qtd, aux_count
			sentences_dics_1 = self.__blob_sentence_to_dict_list(nd['first_sentences'])
			sentences_dics_2 = self.__blob_sentence_to_dict_list(nd['last_sentences'])
			collection.insert({'id':nd['id'],'polarity':nd['polarity'],'num_of_sentences':nd['num_of_sentences'],'first_sentences':sentences_dics_1,'last_sentences':sentences_dics_2})
			aux_qtd += 1		

	def __update_db_from_model(self):
		
		self.model.database['ngrams_distribuition'].drop()
		collection = self.model.database['ngrams_distribuition']
		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1 
		for nd in self.ngrams_distribuition:
			temp_nd = nd.copy()
			temp_nd['first_sentences'] = self.__blob_sentence_to_dict_list(nd['first_sentences'])
			temp_nd['last_sentences'] = self.__blob_sentence_to_dict_list(nd['last_sentences'])
			collection.insert(temp_nd)	

	def load_model_from_db(self):

		collection = self.model.database['ngrams_distribuition']
		self.ngrams_distribuition = []
		for e in collection.find():
			sentences_objs_1 = []
			sentences_objs_2 = []
			sentences_dics_1 = e['first_sentences']
			sentences_dics_2 = e['last_sentences']
			for sd in sentences_dics_1:
				if type(sd) is not dict:
					sentences_objs_1.append(sd)
				else:
					sentences_objs_1.append(self.__dict_to_blob_sentence(sd))
			for sd in sentences_dics_2:
				if type(sd) is not dict:
					sentences_objs_2.append(sd)
				else:
					sentences_objs_2.append(self.__dict_to_blob_sentence(sd))
			e['first_sentences'] = sentences_objs_1
			e['last_sentences'] = sentences_objs_2					
			self.ngrams_distribuition.append(e)

	def _define_tags_by_type(self, _type='adjective'):

		tags_to_consider = util.PENN_ADJECTIVES_TAGS
		if _type == 'adverb':
		 	tags_to_consider = util.PENN_ADVERBS_TAGS
		elif _type == 'noun':
			tags_to_consider = util.PENN_NOUNS_TAGS
		elif _type == 'verb':
			tags_to_consider = util.PENN_VERBS_TAGS

		return tags_to_consider	

	def add_ngram_distribuition_to_model(self, _type='adjective'):
		"""Add to basic model the following key,value pairs:
			{'first_ngrams': list of ngrams based on type from first sentences,
			 'last_ngrams': list of ngrams based on type from first sentences,}
		"""

		tags_to_consider = self._define_tags_by_type(_type)

		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1 	
		for md in self.ngrams_distribuition:
			print "add_ngram_distribuition_to_model", aux_qtd, aux_count
			if md['num_of_sentences'] == 1:
				first_ngrams = []
				for ngram in md['first_sentences']:
					if ngram[1] in tags_to_consider:
						first_ngrams.append(ngram)
				md['first_'+_type+'s'] = first_ngrams

				lasts_ngrams = []
				for ngram in md['last_sentences']:
					if ngram[1] in tags_to_consider:
						lasts_ngrams.append(ngram)
				md['last_'+_type+'s'] = lasts_ngrams		
			else:
				first_ngrams = []
				for s in md['first_sentences']:
					for ngram in s.tags:
						if ngram[1] in tags_to_consider:
							first_ngrams.append(ngram)
				md['first_'+_type+'s'] = first_ngrams

				lasts_ngrams = []
				for s in md['last_sentences']:
					for ngram in s.tags:
						if ngram[1] in tags_to_consider:
							lasts_ngrams.append(ngram)
				md['last_'+_type+'s'] = lasts_ngrams
			aux_qtd += 1
		self.__update_db_from_model()
			
	def get_ngrams_stats(self, _type='adjective'):
		
		tags_to_consider = self._define_tags_by_type(_type)
		ngram_freq_first_part = []
		ngram_freq_second_part = []
		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1
		self.ngrams_distribuition = self.load_model_from_db() if len(self.ngrams_distribuition) == 0 else self.ngrams_distribuition	
		for nd in self.ngrams_distribuition:
			print 'get_ngrams_stats of ' + _type,aux_qtd, aux_count
			ngram_freq_first_part.append(len(nd['first_'+_type+'s']))
			ngram_freq_second_part.append(len(nd['last_'+_type+'s']))
			aux_qtd += 1

		return util.average(ngram_freq_first_part), util.std(ngram_freq_first_part), util.average(ngram_freq_second_part), util.std(ngram_freq_second_part)

	def get_ngrams_stats_from_polar_docs(self, doc_type='positives', _type='adjective', binary_degree=True):

		tags_to_consider = self._define_tags_by_type(_type)
		ngram_freq_first_part = []
		ngram_freq_second_part = []
		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1
		self.ngrams_distribuition = self.load_model_from_db() if len(self.ngrams_distribuition) == 0 else self.ngrams_distribuition	
		polarity, key_name = self._ModelFeatures__set_doc_type(doc_type, 'get_ngrams_stats_from_positive_docs', binary_degree)

		for nd in self.ngrams_distribuition:
			test_pol = True
			if binary_degree:
					test_pol = nd['polarity'] == polarity
			else:
				if doc_type == 'positives':
					test_pol = int(nd['polarity']) >= polarity
				elif doc_type == 'negatives':
					test_pol = int(nd['polarity']) <= polarity
			if test_pol:
				print 'get_ngrams_stats_from_polar_docs of ' + _type + 's',aux_qtd, aux_count
				print nd['id'], nd['polarity'], 'first_'+_type+'s', len(nd['first_'+_type+'s']), 'last_'+_type+'s', len(nd['last_'+_type+'s']) 
				ngram_freq_first_part.append(len(nd['first_'+_type+'s']))
				ngram_freq_second_part.append(len(nd['last_'+_type+'s']))
			aux_qtd += 1

		return util.average(ngram_freq_first_part), util.std(ngram_freq_first_part), util.average(ngram_freq_second_part), util.std(ngram_freq_second_part)

	def get_adjectives_polarities_distribuition(self, prior_polarity_score=False):
		
		_type = 'adjective'
		tags_to_consider = self._define_tags_by_type(_type)
		self.ngrams_distribuition = self.load_model_from_db() if len(self.ngrams_distribuition) == 0 else self.ngrams_distribuition	
		aux_count = len(self.ngrams_distribuition)
		aux_qtd = 1
		adjectives_polarities_distribuition = []
		first_adjectives_polarities_distribuition = []
		last_adjectives_polarities_distribuition = []
		for nd in self.ngrams_distribuition:
			print 'get_adjectives_polarities_distribuition', aux_qtd, aux_count
			for adj in nd['first_'+_type+'s']:
				polarity = transformation.word_polarity(adj[0],pos_tag=adj[1], prior_polarity_score=prior_polarity_score)
				if polarity is not None and polarity[0] != 0:
					first_adjectives_polarities_distribuition.append(polarity[0])
					adjectives_polarities_distribuition.append(polarity[0])

			for adj in nd['last_'+_type+'s']:
				polarity = transformation.word_polarity(adj[0],pos_tag=adj[1], prior_polarity_score=prior_polarity_score)
				if polarity is not None and polarity[0] != 0:
					last_adjectives_polarities_distribuition.append(polarity[0])
					adjectives_polarities_distribuition.append(polarity[0])	
			aux_qtd += 1
		return adjectives_polarities_distribuition, first_adjectives_polarities_distribuition, last_adjectives_polarities_distribuition			
						

									 		
						


