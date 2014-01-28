import os

class Document(object):
	"""Represent a Document"""

	POSITIVE = 1
	NEGATIVE = 0
	UNDEFINED = None

	def __init__(self, name, raw_text, polarity):
		self.name = name
		self.raw_text = raw_text
		self.polarity = polarity
		self.predicted_polarity = Document.UNDEFINED
		self.positives = []
		self.negatives = []


class Cornell(object):
	"""This class holds all documents from Cornell corpora"""

	def __init__(self, txt_sentoken_folder_path):
		self.corpora_path = txt_sentoken_folder_path

	def __create_generic_documents_list(self, folder_name, polarity):
		path = self.corpora_path + folder_name
		try:
			files_names = os.listdir(path)
			document_list = []
		except Exception, e:
			raise e

		for fn in files_names:
			if fn.find('txt') != -1:
				fn_name = path + '/' + fn
				document_list.append(Document(fn,open(fn_name).read(),polarity))
		return document_list

	def __create_positive_documents_list(self):
		return self.__create_generic_documents_list('pos',Document.POSITIVE)

	def __create_negative_documents_list(self):
		return self.__create_generic_documents_list('neg',Document.NEGATIVE)

	def create_documents_list(self):
		self.positives = self.__create_positive_documents_list()
		self.negatives = self.__create_negative_documents_list()

	def all_documents_list(self):
		return self.positives + self.negatives
