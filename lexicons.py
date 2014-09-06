import pymongo
from bson.objectid import ObjectId

class BaseLexicon(object):
	"""docstring for BaseLexicon"""
	def __init__(self, lexicon_name, domain='localhost', port=27017):
		super(BaseLexicon, self).__init__()
		self.client = pymongo.MongoClient(domain, port)
		self.lexicon_name = lexicon_name
		self.database = self.client[lexicon_name]
		self.entries = self.database.entries

	def get_entry_by_id(self, entry_id):
		return self.entries.find({'_id':ObjectId(entry_id)})[0]

	def get_entry_by_name(self, entry_name, entry_field):
		return self.entries.find({entry_field:entry_name})

class SentiWords(BaseLexicon):
	"""Class that models SentiWords from (Gerrine et al.,2013)"""
	
	def __init__(self, lexicon_name="SentiWords"):
		BaseLexicon.__init__(self, lexicon_name)

	def __read_lexicon_source(self):
		path_file = "lexicons/SentiWords/SentiWords_1.0.txt"
		file_obj = open(path_file,"r")

		list_of_dict_units = []
		for line in file_obj.readlines():
			lemma_pos_prior_polarity_score = line.split("\t")
			lemma_pos = lemma_pos_prior_polarity_score[0].split("#")
			lemma = lemma_pos[0]
			pos = lemma_pos[1]
			prior_polarity_score = float(lemma_pos_prior_polarity_score[1].split("\n")[0])
			list_of_dict_units.append({"lemma":lemma, "pos":pos, "prior_polarity_score":prior_polarity_score})

		return list_of_dict_units	

	def get_entry_by_name(self, entry_name , entry_field='lemma'):
		return super(SentiWords, self).get_entry_by_name(entry_name, entry_field)

class SubjectivityClues(BaseLexicon):
	"""Class that models SubjectivityClues from (Wilson et al.,2005)"""

	def __init__(self, lexicon_name="SubjectivityClues"):
		BaseLexicon.__init__(self, lexicon_name)
						
	def __read_lexicon_source(self):
		path_file = "lexicons/SubjectivityClues/subjclueslen1-HLTEMNLP05.tff"
		file_obj = open(path_file,"r")

		list_of_dict_units = []
		for line in file_obj.readlines():
			clue = line.split()
			_type, _len, word1, pos1, stemmed1, priorpolarity = clue[0].split("=")[1], clue[1].split("=")[1], clue[2].split("=")[1], clue[3].split("=")[1], clue[4].split("=")[1], clue[5].split("=")[1]
			list_of_dict_units.append({"type":_type, "len":_len, "word1":word1, "pos1":pos1, "stemmed1":stemmed1, "priorpolarity":priorpolarity})

		return list_of_dict_units

	def create_database(self):
		entries = self.__read_lexicon_source()
		self.entries.drop()

		for entry in entries:
			self.entries.insert(entry)					

	def get_entry_by_name(self, entry_name , entry_field='word1'):
		return super(SubjectivityClues, self).get_entry_by_name(entry_name, entry_field)						


	

		