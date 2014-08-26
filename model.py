import pymongo
import os
import abc
import string
import util
import transformation
from textblob import TextBlob, Word
from textblob.taggers import PatternTagger
from textblob_aptagger import PerceptronTagger
from textblob.wordnet import ADV, ADJ, NOUN, VERB
from bson.objectid import ObjectId
from bson.code import Code

class BaseModel(object):
	"""docstring for BaseModel class that represents and generic corpora in mongodb"""

	__metaclass__ = abc.ABCMeta

	def __init__(self, database_name, domain='localhost', port=27017):
		super(BaseModel, self).__init__()
		self.client = pymongo.MongoClient(domain, port)
		self.database_name = database_name
		self.database = self.client[database_name]
		self.documents = self.database.documents
		self.REDUCER = Code("""
                function (key, values) {
                  var total = 0;
                  for (var i = 0; i < values.length; i++) {
                    total += values[i];
                  }
                  return total;
                }
                """)

	@abc.abstractmethod
	def read_corpora_source(self):
		"""This method should be implemented by each subclass that defines the way of reading each corpora.
		It must returns a list of dictionaries elements.
		"""

		pass

	@abc.abstractmethod
	def create_database(self):
		"""Creates the mongodb database and its documents"""

		pass

	def __is_field_exists(self, collection_name, field_name):
		collection = self.database[collection_name]
		for e in collection.find():
			for k in e.keys():
				if k == field_name:
					return True
		return False			

	def get_doc_by_name(self, doc_name, collection_name='documents'):
		return self.database[collection_name].find({'name':doc_name})[0]

	def get_doc_by_id(self, doc_id):
		return self.documents.find({'_id':ObjectId(doc_id)})[0]

	def pre_process_adverbs(self, tagger="PerceptronTagger"):
		"""This method extracts all adverbs from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = util.get_tagger()
		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			advs = []
			for word, tag in util.tags(blob):
				is_adv = len(Word(word).get_synsets(pos=ADV)) > 0
				if tag in util.PENN_ADVERBS_TAGS and is_adv:
					advs.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'adverbs':advs}})

	def pre_process_nouns(self, tagger="PerceptronTagger"):
		"""This method extracts all nouns from each document in the documents collection


			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = util.get_tagger()
		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			nouns = []
			for word, tag in util.tags(blob):
				is_noun = len(Word(word).get_synsets(pos=NOUN)) > 0
				if tag in util.PENN_NOUNS_TAGS and is_noun:
					nouns.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'nouns':nouns}})

	def pre_process_adjectives(self, tagger="PerceptronTagger"):
		"""This method extracts all adjectives from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = util.get_tagger()
		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			adjectives = []
			for word, tag in util.tags(blob):
				is_adjective = len(Word(word).get_synsets(pos=ADJ)) > 0
				if tag in util.PENN_ADJECTIVES_TAGS and is_adjective:
					adjectives.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'adjectives':adjectives}})

	def pre_process_adv_adj_bigrams(self, tagger="PerceptronTagger"):
		"""This method extracts all adv_adj_bigrams from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = util.get_tagger()

		for ndoc in self.documents.find():
			blob = TextBlob(ndoc['text'])
			valid_bigrams = []
			for s in blob.sentences:
				sentence = pt(s.dict['raw'])
				sentence = pt(sentence.parse())
				bigrams = sentence.ngrams(n=2)
				valid_bigrams = valid_bigrams + util.get_list_bigrams(bigrams, util.ADVERB_ADJECTIVE_BIGRAMS)
			self.documents.update({'name':ndoc['name']},{'$set':{'adv_adj_bigrams':valid_bigrams}})

	def parse_elements_adv_adj_bigrams(self):
		"""This method extracs adjectives and adverbs from adv_adj_bigrams"""

		for ndoc in self.documents.find():
			advs_adv_adj_bigram = []
			adjs_adv_adj_bigram = []
			for bigram in ndoc['adv_adj_bigrams']:
				element_1 = bigram[0].split('/')
				element_2 = bigram[1].split('/')
				if element_1[1] in util.PENN_ADVERBS_TAGS:
					advs_adv_adj_bigram.append(element_1[0])

				if element_2[1] in util.PENN_ADJECTIVES_TAGS:
					adjs_adv_adj_bigram.append(element_2[0])

			self.documents.update({'name':ndoc['name']},{'$set':{'advs_adv_adj_bigram':advs_adv_adj_bigram}})
			self.documents.update({'name':ndoc['name']},{'$set':{'adjs_adv_adj_bigram':adjs_adv_adj_bigram}})

	def pre_process_adv_verb_bigram(self,tagger="PerceptronTagger"):
		"""
			Keyword:
			tagger -- tagger choosed. It could be among the following:
					PerceptronTagger (default) and PatternTagger

		"""

		pt = util.get_tagger()
		for ndoc in self.documents.find():
			blob = TextBlob(ndoc['text'])
			valid_bigrams = []
			for s in blob.sentences:
				sentence = pt(s.dict['raw'])
				sentence = pt(sentence.parse())
				bigrams = sentence.ngrams(n=2)
				valid_bigrams = valid_bigrams + util.get_list_bigrams(bigrams, util.ADVERB_VERB_BIGRAMS)
			self.documents.update({'name':ndoc['name']},{'$set':{'adv_verb_bigrams':valid_bigrams}})

	def create_or_update_collection_from_file(self,file_name, collection_name):
		""" File must have only a pair of values per line, separated by ; """

		f = open(file_name)
		collection = self.database[collection_name]
		for line in f.readlines():
			values = line.split('\n')[0]
			values = values.split(';')
			adverb = values[0]
			factor = values[1]
			collection.insert({'word':adverb,'factor':factor})
		f.close()

	def pre_process_ngrams(self, tagger="PerceptronTagger"):
		"""This method calls the other methods for each type of ngram. It is a shorcut instead of call
			the other one by one.

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		print 'Pre processing adjectives...This can take awhile, depending on corpora size. Cofee, maybe?'
		self.pre_process_adjectives(tagger)
		print 'Pre processing noun...A snack, perhaps?'
		self.pre_process_nouns(tagger)
		print 'Pre processing adverbs...Go read a book or something else, what do you think?'
		self.pre_process_adverbs(tagger)
		print 'Pre processing adv/adj bigram...Boy, this last one is big!'
		self.pre_process_adv_adj_bigrams(tagger)

	def pre_process_adv_xxx_adj_trigrams(self):

		pt = util.get_tagger()
		for ndoc in self.documents.find():
			blob = TextBlob(ndoc['text'])
			valid_trigrams = []
			for s in blob.sentences:
				sentence = pt(s.dict['raw'])
				sentence = pt(sentence.parse())
				trigrams = sentence.ngrams(n=3)
				valid_trigrams = valid_trigrams + util.get_list_trigrams(trigrams, "ADV/XXX/ADJ")
			self.documents.update({'name':ndoc['name']},{'$set':{'adv_xxx_adj_trigrams':valid_trigrams}})
	
	
class TripAdvisorModel(BaseModel):
	"""docstring for TripAdvisorModel"""

	def __init__(self,database_name="TripAdvisor"):
		BaseModel.__init__(self, database_name)

	def read_corpora_source(self):

		source_5255 = os.path.abspath(os.curdir) + '/corpora/trip_advisor/TripAdvisor_5255.txt'
		source_10508 = os.path.abspath(os.curdir) + '/corpora/trip_advisor/TripAdvisor_10508.txt'
		source_file_5255 = open(source_5255,'r')
		source_file_10508 = open(source_10508,'r')

		list_of_dict_units = []

		for line in source_file_5255.readlines():
			parts = line.split()
			name = parts[0]
			degree = parts[len(parts) - 1]

			cons = parts[len(parts) - 2]
			cons = cons.decode('Windows-1252').encode('utf-8')

			pros = parts[len(parts) - 3]
			pros = pros.decode('Windows-1252').encode('utf-8')

			text = string.join(parts[1:len(parts)-3])
			list_of_dict_units.append({'name':name,'text':text,'degree':degree,'pros':pros,'cons':cons})

		for line in source_file_10508.readlines():
			parts = line.split()
			name = parts[0]
			degree = parts[len(parts) - 1]

			cons = parts[len(parts) - 2]
			cons = cons.decode('Windows-1252').encode('utf-8')

			pros = parts[len(parts) - 3]
			pros = pros.decode('Windows-1252').encode('utf-8')

			text = string.join(parts[1:len(parts)-3])
			list_of_dict_units.append({'name':name,'text':text,'degree':degree,'pros':pros,'cons':cons})

		return list_of_dict_units

	def create_database(self):

		docs = self.read_corpora_source()
		#inserts documents into collection
		for d in docs:
			self.documents.insert(d)

		#search for documents with NULL information and attaches the doc id to turn the name unique
		for ndoc in self.documents.find():
			if 'NULL' in ndoc['name']:
				new_ndoc_name = ndoc['name'] + "_" + str(ndoc['_id'])
				self.documents.update({'_id':ndoc['_id']},{'$set':{'name':new_ndoc_name}})

class CornellMoviesModel(BaseModel):
	"""docstring for CornellMoviesModel"""

	def __init__(self, database_name="CornellMovies_v2"):
		BaseModel.__init__(self, database_name)

	def read_corpora_source(self):

		POS_DOCS_PATH = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/pos'
		NEG_DOCS_PATH = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/neg'
		files_pos = os.listdir(POS_DOCS_PATH)
		files_neg = os.listdir(NEG_DOCS_PATH)
		list_of_dict_units = []

		for fn in files_pos:
			if fn.find('txt') != -1:
				fn_name = POS_DOCS_PATH + '/' + fn
				doc = {'name': fn,
						'text':open(fn_name).read(),
						'polarity':1}
				list_of_dict_units.append(doc)

		for fn in files_neg:
			if fn.find('txt') != -1:
				fn_name = NEG_DOCS_PATH + '/' + fn
				doc = {'name': fn,
						'text':open(fn_name).read(),
						'polarity':0}

				list_of_dict_units.append(doc)

		return list_of_dict_units

	def create_database(self):

		docs = self.read_corpora_source()
		#inserts documents into collection
		for d in docs:
			self.documents.insert(d)

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

	def __documents_stats(self):

		if len(self.documents_stats) > 0:
			return self.documents_stats

		list_of_doc_stats = []
		for doc in self.model.documents.find():
			doc_stats = {}

			#adjectives
			adjectives = doc['adjectives']
			positive_adjectives = []
			negative_adjectives = []
			for adj in adjectives:
				adj_pol = transformation.word_polarity(adj)
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

		self.documents_stats = list_of_doc_stats 	
		return list_of_doc_stats

	def __set_doc_type(self, doc_type, key_sufix):

		polarity = self.BINARY_POSITIVE_POLARITY
		key_prefix = "positive_"
		if doc_type == 'negatives':
			polarity = self.BINARY_NEGATIVE_POLARITY
			key_prefix = "negative_"

		key_name = key_prefix + key_sufix
		return (polarity, key_name)		

	def most_frequent_negative_adjectives(self):
		
		if 'most_frequent_negative_adjectives' in self.features.keys():
			return self.features['most_frequent_negative_adjectives']

		results = self.model.documents.map_reduce(self.MAPPER, self.model.REDUCER, 'tempresults')
		sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
		self.model.database['tempresults'].drop()
		most_frequent_negative_adjectives = []
		for x in sorted_results:
			polarity = transformation.word_polarity(x['_id'])
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
			polarity = transformation.word_polarity(x['_id'])
			if polarity is not None and polarity[0] > 0:
				most_frequent_positive_adjectives.append(x)

		self.features['most_frequent_positive_adjectives'] = most_frequent_positive_adjectives		
		return most_frequent_positive_adjectives

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
				
	def positive_documents_highest_num_positive_adjectives(self):
		
		if 'positive_documents_highest_num_positive_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_highest_num_positive_adjectives']

		amount_pos_docs_highest_num_pos_adj = 0.0
		pos_docs_highest_num_pos_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			if doc['polarity'] == 1:
				num_of_docs += 1
				if num_pos_adj > num_neg_adj:
					amount_pos_docs_highest_num_pos_adj += 1
					pos_docs_highest_num_pos_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_highest_num_positive_adjectives'] = (amount_pos_docs_highest_num_pos_adj / num_of_docs, pos_docs_highest_num_pos_adj)
		
		return self.positives_features['positive_documents_highest_num_positive_adjectives']	

	def positive_documents_highest_num_negative_adjectives(self):
		
		if 'positive_documents_highest_num_negative_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_highest_num_negative_adjectives']

		amount_pos_docs_highest_num_neg_adj = 0.0
		pos_docs_highest_num_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			if doc['polarity'] == 1:
				num_of_docs += 1
				if num_pos_adj < num_neg_adj:
					amount_pos_docs_highest_num_neg_adj += 1
					pos_docs_highest_num_neg_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_highest_num_negative_adjectives'] = (amount_pos_docs_highest_num_neg_adj / num_of_docs, pos_docs_highest_num_neg_adj)
		
		return self.positives_features['positive_documents_highest_num_negative_adjectives']

	def positive_documents_equal_num_positive_and_negative_adjectives(self):
		
		if 'positive_documents_equal_num_positive_and_negative_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_equal_num_positive_and_negative_adjectives']

		amount_pos_docs_equal_num_adj = 0.0
		pos_docs_equal_num_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			num_pos_adj = len(stat['positive_adjectives'])
			num_neg_adj = len(stat['negative_adjectives'])

			if doc['polarity'] == 1:
				num_of_docs += 1
				if num_pos_adj == num_neg_adj:
					amount_pos_docs_equal_num_adj += 1
					pos_docs_equal_num_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_equal_num_positive_and_negative_adjectives'] = (amount_pos_docs_equal_num_adj / num_of_docs, pos_docs_equal_num_adj)
		
		return self.positives_features['positive_documents_equal_num_positive_and_negative_adjectives']					

	def positive_documents_highest_sum_positive_adjectives(self):
		
		if 'positive_documents_highest_sum_positive_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_highest_sum_positive_adjectives']

		amount_pos_docs_highest_sum_pos_adj = 0.0
		pos_docs_highest_sum_pos_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'])))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'])))

			if doc['polarity'] == 1:
				num_of_docs += 1
				if sum_pos_adj > sum_neg_adj:
					amount_pos_docs_highest_sum_pos_adj += 1
					pos_docs_highest_sum_pos_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_highest_sum_positive_adjectives'] = (amount_pos_docs_highest_sum_pos_adj / num_of_docs, pos_docs_highest_sum_pos_adj)

		return self.positives_features['positive_documents_highest_sum_positive_adjectives']			

	def positive_documents_highest_sum_negative_adjectives(self):
		
		if 'positive_documents_highest_sum_negative_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_highest_sum_negative_adjectives']

		amount_pos_docs_highest_sum_neg_adj = 0.0
		pos_docs_highest_sum_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'])))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'])))

			if doc['polarity'] == 1:
				num_of_docs += 1
				if sum_pos_adj < sum_neg_adj:
					amount_pos_docs_highest_sum_neg_adj += 1
					pos_docs_highest_sum_neg_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_highest_sum_negative_adjectives'] = (amount_pos_docs_highest_sum_neg_adj / num_of_docs, pos_docs_highest_sum_neg_adj)

		return self.positives_features['positive_documents_highest_sum_negative_adjectives']
		
	def positive_documents_equal_sum_positive_and_negative_adjectives(self):
		
		if 'positive_documents_equal_sum_positive_and_negative_adjectives' in self.positives_features.keys():
			return self.positives_features['positive_documents_equal_sum_positive_and_negative_adjectives']

		amount_pos_docs_equal_sum_pos_neg_adj = 0.0
		pos_docs_equal_sum_pos_neg_adj = []
		num_of_docs = 0.0
		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			sum_pos_adj = abs(sum(transformation.adjectives_polarities(stat['positive_adjectives'])))
			sum_neg_adj = abs(sum(transformation.adjectives_polarities(stat['negative_adjectives'])))

			if doc['polarity'] == 1:
				num_of_docs += 1
				if sum_pos_adj == sum_neg_adj:
					amount_pos_docs_equal_sum_pos_neg_adj += 1
					pos_docs_equal_sum_pos_neg_adj.append(str(doc['_id']))

		self.positives_features['positive_documents_equal_sum_positive_and_negative_adjectives'] = (amount_pos_docs_equal_sum_pos_neg_adj / num_of_docs, pos_docs_equal_sum_pos_neg_adj)

		return self.positives_features['positive_documents_equal_sum_positive_and_negative_adjectives']	

	def positive_documents_highest_score_positive_adjective(self):
		
		if 'positive_documents_highest_score_positive_adjective' in self.positives_features.keys():
			return self.positives_features['positive_documents_highest_score_positive_adjective']

		amount_pos_docs_highest_score_pos_adj = 0.0
		pos_docs_highest_score_pos_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'])
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'])
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

			if doc['polarity'] == 1:
				num_of_docs += 1
				if abs(max_pos_adj) > abs(max_neg_adj):
					amount_pos_docs_highest_score_pos_adj += 1
					pos_docs_highest_score_pos_adj.append(str(doc['_id']))	

		self.positives_features['positive_documents_highest_score_positive_adjective'] = (amount_pos_docs_highest_score_pos_adj / num_of_docs, amount_pos_docs_highest_score_pos_adj, pos_docs_highest_score_pos_adj)

		return self.positives_features['positive_documents_highest_score_positive_adjective']			

	def documents_highest_score_negative_adjectives(self, doc_type):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_highest_score_negative_adjectives')

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_highest_score_neg_adj = 0.0
		docs_highest_score_neg_adj = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'])
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'])
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

			if doc['polarity'] == polarity:
				num_of_docs += 1
				if abs(max_pos_adj) < abs(max_neg_adj):
					amount_docs_highest_score_neg_adj += 1
					docs_highest_score_neg_adj.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_highest_score_neg_adj / num_of_docs, amount_docs_highest_score_neg_adj, docs_highest_score_neg_adj)

		return self.features[key_name]

	def documents_equal_adjectives_scores(self, doc_type):
		
		polarity, key_name = self.__set_doc_type(doc_type, 'documents_equal_adjectives_scores')

		if key_name in self.features.keys():
			return self.features[key_name]

		amount_docs_equal_adj_score = 0.0
		docs_equal_adj_scores = []
		num_of_docs = 0.0

		for stat in self.__documents_stats():
			doc = self.model.get_doc_by_id(stat['_id'])
			pos_adjs = transformation.adjectives_polarities(stat['positive_adjectives'])
			neg_adjs = transformation.adjectives_polarities(stat['negative_adjectives'])
			max_pos_adj = 0 if len(pos_adjs) == 0 else util.max_abs(pos_adjs)
			max_neg_adj = 0 if len(neg_adjs) == 0 else util.max_abs(neg_adjs)

			if doc['polarity'] == polarity:
				num_of_docs += 1
				if abs(max_pos_adj) == abs(max_neg_adj):
					amount_docs_equal_adj_score += 1
					docs_equal_adj_scores.append(str(doc['_id']))	

		self.features[key_name] = (amount_docs_equal_adj_score / num_of_docs, amount_docs_equal_adj_score, docs_equal_adj_scores)

		return self.features[key_name]	
