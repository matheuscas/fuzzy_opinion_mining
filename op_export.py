import model2
import abc
import transformation

class BaseExport(object):
	"""This class holds the main functions concerned about
	creation and exportation of opinions polarities to text files"""

	__metaclass__ = abc.ABCMeta

	def __init__(self, baseModel):
		super(BaseExport, self).__init__()
		self.model = baseModel

	@abc.abstractmethod
	def export_files(self):
		pass

	# def calculates_adjectives_polarities(self, ndoc, unique=True):
	# 	"""This method calculates all adjectives polarities based on the following arguments

	# 	Keyword arguments:
	# 	ndoc -- given document
	# 	unique -- False for all adjectives list.
	# 			  True for only those adjectives that are not in bigrams (or trigrams) list. (default: True)
	# 	"""
	# 	adjectives = ndoc['adjectives']
	# 	adjs_adv_adj_bigram = ndoc['adjs_adv_adj_bigram']
	# 	for e in adjs_adv_adj_bigram:
	# 		if e in adjectives:
	# 			adjectives.remove(e)

	# 	adjectives_polarities = []
	# 	for adjective in adjectives:
	# 		polarity = transformation.word_polarity(adjective)
	# 		if polarity and polarity[0] != 0.0:
	# 			adjectives_polarities.append(polarity[0])

	# 	return adjectives_polarities

	# def default_calculates_adv_adj_bigrams_polarities(self, ndoc):
	# 	"""This method calculates all bigrams polarities based on the following arguments

	# 	Keyword arguments:
	# 	ndoc -- given document
	# 	"""

	# 	adv_adj_bigrams_polarities = []
	# 	for bigram in ndoc['adv_adj_bigrams']:
	# 		bigram_polarity = transformation.default_adv_adj_bigram_polarity(bigram)
	# 		if bigram_polarity:
	# 			adv_adj_bigrams_polarities.append(bigram_polarity)

	# 	return adv_adj_bigrams_polarities

	def get_adjectives(self, ndoc, filtered=True):
		"""This method return from document all the adjectives based on the following parameters:

		Keyword arguments:
		ndoc -- document from model
		filtered -- Returns only adjectives that are not in ADV / ADJ bigrams (default: True)
		"""

		adjectives = ndoc['adjectives']
		adjs_adv_adj_bigram = ndoc['adjs_adv_adj_bigram']

		if filtered:
			for e in adjs_adv_adj_bigram:
				if e in adjectives:
					adjectives.remove(e)

		return adjectives

class TripAdvisorExport(BaseExport):
	"""Class responsible for create and export files with ngrams polarities from its model"""

	def __init__(self, trip_advisor_model):
		BaseExport.__init__(self, trip_advisor_model)

	def export_files(self):

		negative_matrix = []
		negative_matrix_max_size = 0.0
		positive_matrix = []
		positive_matrix_max_size = 0.0

		for ndoc in self.model.documents.find():

			if float(ndoc['degree']) <= 2:

				adjectives = self.get_adjectives(ndoc)

				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > negative_matrix_max_size:
					negative_matrix_max_size = len(ndoc_polarities)
				negative_matrix.append(ndoc_polarities)
			elif float(ndoc['degree']) >= 4:

				adjectives = self.get_adjectives(ndoc)

				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > positive_matrix_max_size:
					positive_matrix_max_size = len(ndoc_polarities)
				positive_matrix.append(ndoc_polarities)

		pos_matrix_file = open('files_to_export/TripAdvisor/pos_matrix_file.txt','w+')
		neg_matrix_file = open('files_to_export/TripAdvisor/neg_matrix_file.txt','w+')

		for ndoc_polarities in positive_matrix:
			if positive_matrix_max_size - len(ndoc_polarities) > 0:
				ndoc_polarities = ndoc_polarities + ([0.0] * (positive_matrix_max_size - len(ndoc_polarities)))
			for e in ndoc_polarities:
				pos_matrix_file.write(str(e) + ';')
			pos_matrix_file.write('\n')

		pos_matrix_file.close()

		for ndoc_polarities in negative_matrix:
			if negative_matrix_max_size - len(ndoc_polarities) > 0:
				ndoc_polarities = ndoc_polarities + ([0.0] * (negative_matrix_max_size - len(ndoc_polarities)))
			for e in ndoc_polarities:
				neg_matrix_file.write(str(e) + ';')
			neg_matrix_file.write('\n')

		neg_matrix_file.close()

class CornellMoviesExport(BaseExport):
	"""docstring for CornellMoviesExport"""

	def __init__(self, cornell_movies_model):
		BaseExport.__init__(self, cornell_movies_model)

	def export_files(self):

		negative_matrix = []
		negative_matrix_max_size = 0.0
		positive_matrix = []
		positive_matrix_max_size = 0.0

		for ndoc in self.model.documents.find():

			adjectives = self.get_adjectives(ndoc)

			if ndoc['polarity'] == 0:
				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > negative_matrix_max_size:
					negative_matrix_max_size = len(ndoc_polarities)
				negative_matrix.append(ndoc_polarities)
			elif ndoc['polarity'] == 1:
				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > positive_matrix_max_size:
					positive_matrix_max_size = len(ndoc_polarities)
				positive_matrix.append(ndoc_polarities)

		pos_matrix_file = open('files_to_export/CornellMovies/pos_matrix_file.txt','w+')
		neg_matrix_file = open('files_to_export/CornellMovies/neg_matrix_file.txt','w+')

		for ndoc_polarity in positive_matrix:
			if positive_matrix_max_size - len(ndoc_polarity) > 0:
				ndoc_polarity = ndoc_polarity + ([0.0] * (positive_matrix_max_size - len(ndoc_polarity)))
			for e in ndoc_polarity:
				pos_matrix_file.write(str(e) + ';')
			pos_matrix_file.write('\n')

		pos_matrix_file.close()

		for ndoc_polarity in negative_matrix:
			if negative_matrix_max_size - len(ndoc_polarity) > 0:
				ndoc_polarity = ndoc_polarity + ([0.0] * (negative_matrix_max_size - len(ndoc_polarity)))
			for e in ndoc_polarity:
				neg_matrix_file.write(str(e) + ';')
			neg_matrix_file.write('\n')

		neg_matrix_file.close()




