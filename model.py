import pymongo
import os
import abc
import string
import util
from textblob import TextBlob, Word, Blobber
from textblob.taggers import NLTKTagger
from textblob.taggers import PatternTagger
from textblob_aptagger import PerceptronTagger
from textblob.wordnet import ADV, ADJ, NOUN, VERB

class BaseModel(object):
	"""docstring for BaseModel class that represents and generic corpora in mongodb"""

	__metaclass__ = abc.ABCMeta

	def __init__(self, database_name, domain='localhost', port=27017):
		super(BaseModel, self).__init__()
		self.client = pymongo.MongoClient(domain, port)
		self.database_name = database_name
		self.database = self.client[database_name]
		self.documents = self.database.documents

		self.PENN_ADVERBS_TAGS = ['RB', 'RBR', 'RBS', 'RP']
		self.PENN_ADJECTIVES_TAGS = ['JJ','JJR','JJS']
		self.PENN_NOUNS_TAGS = ['NN','NNS','NNP','NNPS']
		self.PENN_VERBS_TAGS = ['MD','VB','VBZ','VBP','VBD','VBN','VBG']
		self.ADVERB_ADJECTIVE_BIGRAMS = ["RB/JJ","RB/JJR", "RB/JJS",
											"RBR/JJ","RBR/JJR", "RBR/JJS",
											"RBS/JJ","RBS/JJR", "RBS/JJS",
											"RP/JJ","RP/JJR", "RP/JJS"]

		self.ADVERB_VERB_BIGRAMS = ['RB/MD','RB/VB','RB/VBZ','RB/VBP','RB/VBD','RB/VBN','RB/VBG',
									'RBR/MD','RBR/VB','RBR/VBZ','RBR/VBP','RBR/VBD','RBR/VBN','RBR/VBG',
									'RBS/MD','RBS/VB','RBS/VBZ','RBS/VBP','RBS/VBD','RBS/VBN','RBS/VBG',
									'RP/MD','RP/VB','RP/VBZ','RP/VBP','RP/VBD','RP/VBN','RP/VBG']


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

	def is_adverb(self, word_tag):
		"""Checks if the passed tag is an adverb tag.

		Keyword arguments:
		word_tag -- Penn tag from word in ngram
		"""

		return word_tag in self.PENN_ADVERBS_TAGS

	def is_adjective(self, word_tag):
		"""Checks if the passed tag is an adjective tag.

		Keyword arguments:
		word_tag -- Penn tag from word in ngram
		"""

		return word_tag in self.PENN_ADJECTIVES_TAGS

	def is_noun(self, word_tag):
		"""Checks if the passed tag is an noun tag.

		Keyword arguments:
		word_tag -- Penn tag from word in ngram
		"""

		return word_tag in self.PENN_NOUNS_TAGS

	def is_verb(self, word_tag):
		"""Checks if the passed tag is an verb tag.

		Keyword arguments:
		word_tag -- Penn tag from word in ngram
		"""

		return word_tag in self.PENN_VERBS_TAGS

	def is_adverb_adjective_bigram(self, bigram, type="ADV_ADJ"):
		"""Checks if the passed bigram is an adverb_adjective bigram.

		Keyword arguments:
		bigram -- should be in the following pattern: tag1/tag2
		type -- passes the type of bigram to be validated
		"""

		return bigram in self.ADVERB_ADJECTIVE_BIGRAMS

	def tags(self, blob):
		parsed_text = blob.parse().split()
		tags = []
		for elem in parsed_text[0]:
			tags.append((elem[0],elem[1]))

		return tags

	def pre_process_adverbs(self, tagger="PerceptronTagger"):
		"""This method extracts all adverbs from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = Blobber(pos_tagger=PerceptronTagger())
		if tagger == "PatternTagger":
			pt = Blobber(pos_tagger=PatternTagger())
		else:
			print "PerceptronTagger will be used"

		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			advs = []
			for word, tag in self.tags(blob):
				is_adv = len(Word(word).get_synsets(pos=ADV)) > 0
				if tag in self.PENN_ADVERBS_TAGS and is_adv:
					advs.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'adverbs':advs}})

	def pre_process_nouns(self, tagger="PerceptronTagger"):
		"""This method extracts all nouns from each document in the documents collection


			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = Blobber(pos_tagger=PerceptronTagger())
		if tagger == "PatternTagger":
			pt = Blobber(pos_tagger=PatternTagger())
		else:
			print "PerceptronTagger will be used"

		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			nouns = []
			for word, tag in self.tags(blob):
				is_noun = len(Word(word).get_synsets(pos=NOUN)) > 0
				if tag in self.PENN_NOUNS_TAGS and is_noun:
					nouns.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'nouns':nouns}})

	def pre_process_adjectives(self, tagger="PerceptronTagger"):
		"""This method extracts all adjectives from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = Blobber(pos_tagger=PerceptronTagger())
		if tagger == "PatternTagger":
			pt = Blobber(pos_tagger=PatternTagger())
		else:
			print "PerceptronTagger will be used"

		for ndoc in self.documents.find():
			blob = pt(ndoc['text'])
			adjectives = []
			for word, tag in self.tags(blob):
				is_adjective = len(Word(word).get_synsets(pos=ADJ)) > 0
				if tag in self.PENN_ADJECTIVES_TAGS and is_adjective:
					adjectives.append(word)
			self.documents.update({'name':ndoc['name']},{'$set':{'adjectives':adjectives}})

	def pre_process_adv_adj_bigrams(self, tagger="PerceptronTagger"):
		"""This method extracts all adv_adj_bigrams from each document in the documents collection

			Keyword:
			tagger -- tagger choosed. It could be among the following:
                      PerceptronTagger (default) and PatternTagger
		"""

		pt = Blobber(pos_tagger=PerceptronTagger())
		if tagger == "PatternTagger":
			pt = Blobber(pos_tagger=PatternTagger())
		else:
			print "PerceptronTagger will be used"

		for ndoc in self.documents.find():
			blob = TextBlob(ndoc['text'])
			valid_bigrams = []
			for s in blob.sentences:
				sentence = pt(s.dict['raw'])
				sentence = pt(sentence.parse())
				bigrams = sentence.ngrams(n=2)
				valid_bigrams = valid_bigrams + util.get_bigrams(bigrams, self.ADVERB_ADJECTIVE_BIGRAMS)
			self.documents.update({'name':ndoc['name']},{'$set':{'adv_adj_bigrams':valid_bigrams}})

	def parse_elements_adv_adj_bigrams(self):
		"""This method extracs adjectives and adverbs from adv_adj_bigrams"""

		for ndoc in self.documents.find():
			advs_adv_adj_bigram = []
			adjs_adv_adj_bigram = []
			for bigram in ndoc['adv_adj_bigrams']:
				element_1 = bigram[0].split('/')
				element_2 = bigram[1].split('/')
				if element_1[1] in self.PENN_ADVERBS_TAGS:
					advs_adv_adj_bigram.append(element_1[0])

				if element_2[1] in self.PENN_ADJECTIVES_TAGS:
					adjs_adv_adj_bigram.append(element_2[0])

			self.documents.update({'name':ndoc['name']},{'$set':{'advs_adv_adj_bigram':advs_adv_adj_bigram}})
			self.documents.update({'name':ndoc['name']},{'$set':{'adjs_adv_adj_bigram':adjs_adv_adj_bigram}})

	def pre_process_adv_verb_bigram(self,tagger="PerceptronTagger"):
		"""
			Keyword:
			tagger -- tagger choosed. It could be among the following:
					PerceptronTagger (default) and PatternTagger

		"""

		pt = Blobber(pos_tagger=PerceptronTagger())
		if tagger == "PatternTagger":
			pt = Blobber(pos_tagger=PatternTagger())
		else:
			print "PerceptronTagger will be used"

		for ndoc in self.documents.find():
			blob = TextBlob(ndoc['text'])
			valid_bigrams = []
			for s in blob.sentences:
				sentence = pt(s.dict['raw'])
				sentence = pt(sentence.parse())
				bigrams = sentence.ngrams(n=2)
				valid_bigrams = valid_bigrams + util.get_bigrams(bigrams, self.ADVERB_VERB_BIGRAMS)
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

	def __init__(self, database_name="CornellMovies"):
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
