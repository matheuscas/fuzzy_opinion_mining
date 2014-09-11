import pymongo
import transformation
import util
import lexicons
from textblob import blob, TextBlob, Word
from textblob.taggers import PatternTagger
from textblob_aptagger import PerceptronTagger
from textblob.wordnet import ADV, ADJ, NOUN, VERB
from collections import Counter
from bson.code import Code

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

	def __documents_stats(self):

		if len(self.documents_stats) > 0:
			return self.documents_stats

		list_of_doc_stats = []
		temp_num = 1
		for doc in self.model.documents.find():
			doc_stats = {}
			print temp_num
			#adjectives
			adjectives = doc['adjectives']
			positive_adjectives = []
			negative_adjectives = []
			for adj in adjectives:
				adj_pol = transformation.word_polarity(adj, prior_polarity_score=self.prior_polarity_score)
				if adj_pol is None:
					adj_pol = (0,0)

				if adj_pol[0] > 0:
					positive_adjectives.append(adj)
				elif adj_pol[0] < 0:
					negative_adjectives.append(adj)		
			doc_stats['positive_adjectives'] = positive_adjectives
			doc_stats['negative_adjectives'] = negative_adjectives
			doc_stats['_id'] = str(doc['_id'])
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

	def most_frequent_negative_adjectives(self):
		
		if 'most_frequent_negative_adjectives' in self.features.keys():
			return self.features['most_frequent_negative_adjectives']

		results = self.model.documents.map_reduce(self.MAPPER, self.model.REDUCER, 'tempresults')
		sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
		self.model.database['tempresults'].drop()
		most_frequent_negative_adjectives = []
		for x in sorted_results:
			polarity = transformation.word_polarity(x['_id'], prior_polarity_score=self.prior_polarity_score)
			if polarity is not None and polarity[0] < 0:
				most_frequent_negative_adjectives.append(x)

		self.features['most_frequent_negative_adjectives'] = most_frequent_negative_adjectives		
		return most_frequent_negative_adjectives

	def most_frequent_positive_adjectives(self):
		
		if 'most_frequent_positive_adjectives' in self.features.keys():
			return self.features['most_frequent_positive_adjectives']

		results = self.model.documents.map_reduce(self.MAPPER, self.model.REDUCER, 'tempresults')
		sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
		self.model.database['tempresults'].drop()
		most_frequent_positive_adjectives = []
		for x in sorted_results:
			polarity = transformation.word_polarity(x['_id'], prior_polarity_score=self.prior_polarity_score)
			if polarity is not None and polarity[0] > 0:
				most_frequent_positive_adjectives.append(x)

		self.features['most_frequent_positive_adjectives'] = most_frequent_positive_adjectives		
		return most_frequent_positive_adjectives

	def most_frequent_positive_adjectives_in_positive_documents(self):
		
		if 'most_frequent_positive_adjectives_in_positive_documents' in self.features.keys():
			return self.features['most_frequent_positive_adjectives_in_positive_documents']

		all_positive_adjectives = []
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if doc['polarity'] == self.BINARY_POSITIVE_POLARITY:
				all_positive_adjectives = all_positive_adjectives + stat['positive_adjectives']

		all_positive_adjectives_freq = Counter(all_positive_adjectives)
		self.features['most_frequent_positive_adjectives_in_positive_documents'] = all_positive_adjectives_freq
		return all_positive_adjectives_freq

	def most_frequent_negative_adjectives_in_negative_documents(self):

		if 'most_frequent_negative_adjectives_in_negative_documents' in self.features.keys():
			return self.features['most_frequent_negative_adjectives_in_negative_documents']

		all_negative_adjectives = []
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			if doc['polarity'] == self.BINARY_NEGATIVE_POLARITY:
				all_negative_adjectives = all_negative_adjectives + stat['negative_adjectives']

		all_negative_adjectives_freq = Counter(all_negative_adjectives)
		self.features['most_frequent_negative_adjectives_in_negative_documents'] = all_negative_adjectives_freq
		return all_negative_adjectives_freq		

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
				
	def documents_highest_count_positive_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_count_positive_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_num_pos_adj = 0.0
		docs_highest_num_pos_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				print num_pos_adj, num_neg_adj
				num_of_docs += 1
				if num_pos_adj > num_neg_adj:
					amount_docs_highest_num_pos_adj += 1
					docs_highest_num_pos_adj.append(str(doc['_id']))

		print num_of_docs			
		self.features[key_name] = (amount_docs_highest_num_pos_adj / num_of_docs, amount_docs_highest_num_pos_adj, docs_highest_num_pos_adj)
		
		return self.features[key_name]	

	def documents_highest_count_negative_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_count_negative_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_count_neg_adj = 0.0
		docs_highest_num_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if num_pos_adj < num_neg_adj:
					amount_docs_highest_count_neg_adj += 1
					docs_highest_num_neg_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_highest_count_neg_adj / num_of_docs, amount_docs_highest_count_neg_adj, docs_highest_num_neg_adj)
		
		return self.features[key_name]

	def documents_equal_count_positive_and_negative_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_count_positive_and_negative_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_count_adj = 0.0
		docs_equal_num_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if num_pos_adj == num_neg_adj:
					amount_docs_equal_count_adj += 1
					docs_equal_num_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_equal_count_adj / num_of_docs, amount_docs_equal_count_adj, docs_equal_num_adj)
		
		return self.features[key_name]					

	def documents_highest_sum_positive_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_sum_positive_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_sum_pos_adj = 0.0
		docs_highest_sum_pos_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj > sum_neg_adj:
					amount_docs_highest_sum_pos_adj += 1
					docs_highest_sum_pos_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_highest_sum_pos_adj / num_of_docs, amount_docs_highest_sum_pos_adj, docs_highest_sum_pos_adj)

		return self.features[key_name]			

	def documents_highest_sum_negative_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_sum_negative_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_sum_neg_adj = 0.0
		docs_highest_sum_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj < sum_neg_adj:
					amount_docs_highest_sum_neg_adj += 1
					docs_highest_sum_neg_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_highest_sum_neg_adj / num_of_docs, amount_docs_highest_sum_neg_adj, docs_highest_sum_neg_adj)

		return self.features[key_name]
		
	def documents_equal_sum_positive_and_negative_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_sum_positive_and_negative_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_sum_pos_neg_adj = 0.0
		docs_equal_sum_pos_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)))

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if sum_pos_adj == sum_neg_adj:
					amount_docs_equal_sum_pos_neg_adj += 1
					docs_equal_sum_pos_neg_adj.append(str(doc['_id']))

		self.features[key_name] = (amount_docs_equal_sum_pos_neg_adj / num_of_docs, amount_docs_equal_sum_pos_neg_adj, docs_equal_sum_pos_neg_adj)

		return self.features[key_name]	

	def documents_highest_score_positive_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_score_positive_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_score_pos_adj = 0.0
		docs_highest_score_pos_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if abs(max_pos_adj) > abs(max_neg_adj):
					amount_docs_highest_score_pos_adj += 1
					docs_highest_score_pos_adj.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_highest_score_pos_adj / num_of_docs, amount_docs_highest_score_pos_adj, docs_highest_score_pos_adj)

		return self.features[key_name]			

	def documents_highest_score_negative_adjectives(self, doc_type, binary_degree=True):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_score_negative_adjectives', binary_degree)

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_score_neg_adj = 0.0
		docs_highest_score_neg_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

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
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'], prior_polarity_score=self.prior_polarity_score)
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'], prior_polarity_score=self.prior_polarity_score)
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

			test_pol = self.__set_polarity_test(binary_degree, doc, polarity, doc_type)
			if test_pol:
				num_of_docs += 1
				if abs(max_pos_adj) == abs(max_neg_adj):
					amount_docs_equal_adj_score += 1
					docs_equal_adj_scores.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_equal_adj_score / num_of_docs, amount_docs_equal_adj_score, docs_equal_adj_scores)

		return self.features[key_name]

# class SubjectivityClues(ModelFeatures):
# 	"""Features for SubjectivityClues"""

# 	def __init__(self, model):
# 		ModelFeatures.__init__(self, model)
# 		self.lexicon = lexicons.SubjectivityClues()
# 		self.lexicon_cache = {}

# 	def __get_docs_subjectivity_clues(self, doc):
# 		tagger = util.get_tagger()
# 		blob_text = tagger(doc['text'])
# 		blob_word = None
# 		clues = []
# 		hits_on_cache = 0
# 		hits_on_db = 0
# 		for word, tag in util.tags(blob_text):
# 			if word in self.lexicon_cache:
# 				clues.append(self.lexicon_cache[word])
# 				hits_on_cache += 1
# 			else:
# 				clue = self.lexicon.get_one_entry_by_name(word)
# 				hits_on_db += 1
# 				if clue is None:
# 					wordnet_tag = blob._penn_to_wordnet(tag)
# 					word_lemma = Word(word).lemmatize(wordnet_tag)
# 					if word_lemma in self.lexicon_cache:
# 						clues.append(self.lexicon_cache[word_lemma])
# 						hits_on_cache += 1
# 					else:
# 						clue = self.lexicon.get_one_entry_by_name(word_lemma)
# 						hits_on_db += 1
# 						if clue is not None:
# 							clues.append(clue)
# 							self.lexicon_cache[word_lemma] = clue
# 				else:
# 					clues.append(clue)
# 					self.lexicon_cache[word] = clue
# 		return clues, hits_on_cache, hits_on_db
		
# 	def __get_weak_subjectivity_clues(self, doc_subjectivity_clues):
# 		weak_scs = []
# 		for sc in doc_subjectivity_clues:
# 			if sc['type'] == 'weaksubj':
# 				weak_scs.append(sc)
# 		return weak_scs

# 	def __get_positive_weak_subjectivity_clues(self, doc_weak_subjectivity_clues):
# 		pos_weak_scs = []
# 		for sc in doc_weak_subjectivity_clues:
# 			if sc['priorpolarity'] == 'positive':
# 				pos_weak_scs.append(sc)
# 		return pos_weak_scs	

# 	def __get_negative_weak_subjectivity_clues(self, doc_weak_subjectivity_clues):
# 		neg_weak_scs = []
# 		for sc in doc_weak_subjectivity_clues:
# 			if sc['priorpolarity'] == 'negative':
# 				neg_weak_scs.append(sc)
# 		return neg_weak_scs

# 	def __get_strong_subjectivity_clues(self, doc_subjectivity_clues):
# 		strong_scs = []
# 		for sc in doc_subjectivity_clues:
# 			if sc['type'] == 'strongsubj':
# 				strong_scs.append(sc)
# 		return strong_scs
		
# 	def __get_positive_strong_subjectivity_clues(self, doc_strong_subjectivity_clues):
# 		pos_strong_scs = []
# 		for sc in doc_strong_subjectivity_clues:
# 			if sc['priorpolarity'] == 'positive':
# 				pos_strong_scs.append(sc)
# 		return pos_strong_scs
		
# 	def __get_negative_strong_subjectivity_clues(self, doc_strong_subjectivity_clues):
# 		neg_strong_scs = []
# 		for sc in doc_strong_subjectivity_clues:
# 			if sc['priorpolarity'] == 'negative':
# 				neg_strong_scs.append(sc)
# 		return neg_strong_scs					

# 	def documents_with_subjectivity_clues(self, doc_type, binary_degree=True):
		
# 		polarity, key_name = self._ModelFeatures__set_doc_type(doc_type, 'documents_with_subjectivity_clues', binary_degree)

# 		if key_name in self.features.keys():
# 			return self.features[key_name]

# 		scs_in_docs = []
# 		weak_scs_in_docs = []
# 		pos_weak_scs_in_docs = []
# 		neg_weak_scs_in_docs = []
# 		strong_scs_in_docs = []
# 		pos_strong_scs_in_docs = []
# 		neg_strong_scs_in_docs = []

# 		docs_qtd = 0.0
# 		for doc in self.model.documents.find():
# 			test_pol = self._ModelFeatures__set_polarity_test(binary_degree, doc, polarity, doc_type)
# 			if test_pol:
# 				docs_sc, hits_on_cache, hits_on_db = self.__get_docs_subjectivity_clues(doc)
# 				scs_in_docs.append(len(docs_sc))

# 				docs_weak_sc = self.__get_weak_subjectivity_clues(docs_sc)
# 				weak_scs_in_docs.append(len(docs_weak_sc))

# 				docs_pos_weak_sc = self.__get_positive_weak_subjectivity_clues(docs_weak_sc)
# 				pos_weak_scs_in_docs.append(len(docs_pos_weak_sc))

# 				docs_neg_weak_sc = self.__get_negative_weak_subjectivity_clues(docs_weak_sc)
# 				neg_weak_scs_in_docs.append(len(docs_neg_weak_sc))

# 				docs_strong_sc = self.__get_strong_subjectivity_clues(docs_sc)
# 				strong_scs_in_docs.append(len(docs_strong_sc))

# 				docs_pos_strong_sc = self.__get_positive_strong_subjectivity_clues(docs_strong_sc)
# 				pos_strong_scs_in_docs.append(len(docs_pos_strong_sc))

# 				docs_neg_strong_sc = self.__get_negative_strong_subjectivity_clues(docs_strong_sc)
# 				neg_strong_scs_in_docs.append(len(docs_neg_strong_sc))

# 				docs_qtd += 1.0
# 				print docs_qtd, len(self.lexicon_cache.keys()), hits_on_cache, hits_on_db

# 		sc_avg = util.average(scs_in_docs)
# 		sc_std = util.std(scs_in_docs)
# 		general_stats = (sc_avg, sc_std, docs_qtd)

# 		weak_sc_avg = util.average(weak_scs_in_docs)
# 		weak_sc_std = util.std(weak_scs_in_docs)
# 		pos_weak_sc_avg = util.average(pos_weak_scs_in_docs)
# 		pos_weak_sc_std = util.std(pos_weak_scs_in_docs)
# 		neg_weak_sc_avg = util.average(neg_weak_scs_in_docs)
# 		neg_weak_sc_std = util.std(neg_weak_scs_in_docs)
# 		weak_stats = (weak_sc_avg, weak_sc_std, pos_weak_sc_avg, pos_weak_sc_std, neg_weak_sc_avg, neg_weak_sc_std)

# 		strong_sc_avg = util.average(strong_scs_in_docs)
# 		strong_sc_std = util.std(strong_scs_in_docs)
# 		pos_strong_sc_avg = util.average(pos_strong_scs_in_docs)
# 		pos_strong_sc_std = util.std(pos_strong_scs_in_docs)
# 		neg_strong_sc_avg = util.average(neg_strong_scs_in_docs)
# 		neg_strong_sc_std = util.std(neg_strong_scs_in_docs)
# 		strong_stats = (strong_sc_avg, strong_sc_std, pos_strong_sc_avg, pos_strong_sc_std, neg_strong_sc_avg, neg_strong_sc_std)

# 		return general_stats, weak_stats, strong_stats		

		


