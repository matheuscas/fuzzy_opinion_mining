import pymongo
import os
import abc
import string
import util
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

