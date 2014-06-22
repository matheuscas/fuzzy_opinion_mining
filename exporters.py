import model2
import abc
import transformation
import shutil
import os

class BaseExport(object):
	"""This class holds the main functions concerned about
	creation and exportation of opinions polarities to text files"""

	__metaclass__ = abc.ABCMeta

	def __init__(self, baseModel):
		super(BaseExport, self).__init__()
		self.model = baseModel
		self.origin_folder = ""
		self.dest_folder = ""

	@abc.abstractmethod
	def export_files(self):
		pass

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

	def copy_files(self):
		try:
			files_names = os.listdir(self.origin_folder)
		except Exception, e:
			raise e

		for fn in files_names:
			if fn.find('txt') != -1:
				fn_name = self.origin_folder + '/' + fn
				shutil.copy2(fn_name, self.dest_folder)


class TripAdvisorExport(BaseExport):
	"""Class responsible for create and export files with ngrams polarities from its model"""

	def __init__(self, trip_advisor_model):
		BaseExport.__init__(self, trip_advisor_model)
		self.origin_folder = "files_to_export/TripAdvisor/"
		self.dest_folder = "/Users/matheuscas/Dropbox/UFBA/Mestrado/Pesquisa/matlab/polarities_files/TripAdvisor"

	def export_files(self):

		negative_matrix_polarities = []
		negative_matrix_max_size = 0.0
		positive_matrix_polarities = []
		positive_matrix_max_size = 0.0

		positive_matrix_index = []
		negative_matrix_index = []

		for ndoc in self.model.documents.find():

			if float(ndoc['degree']) <= 2:

				adjectives = self.get_adjectives(ndoc)

				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > negative_matrix_max_size:
					negative_matrix_max_size = len(ndoc_polarities)
				negative_matrix_polarities.append(ndoc_polarities)
				negative_matrix_index.append(ndoc['name'] + "-" + str(ndoc['_id']))

			elif float(ndoc['degree']) >= 4:

				adjectives = self.get_adjectives(ndoc)

				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > positive_matrix_max_size:
					positive_matrix_max_size = len(ndoc_polarities)
				positive_matrix_polarities.append(ndoc_polarities)
				positive_matrix_index.append(ndoc['name'] + "-" + str(ndoc['_id']))

		pos_matrix_file = open('files_to_export/TripAdvisor/pos_matrix_file.txt','w+')
		neg_matrix_file = open('files_to_export/TripAdvisor/neg_matrix_file.txt','w+')

		for ndoc_polarities in positive_matrix_polarities:
			if positive_matrix_max_size - len(ndoc_polarities) > 0:
				ndoc_polarities = ndoc_polarities + ([0.0] * (positive_matrix_max_size - len(ndoc_polarities)))
			for e in ndoc_polarities:
				pos_matrix_file.write(str(e) + ';')
			pos_matrix_file.write('\n')

		pos_matrix_file.close()

		for ndoc_polarities in negative_matrix_polarities:
			if negative_matrix_max_size - len(ndoc_polarities) > 0:
				ndoc_polarities = ndoc_polarities + ([0.0] * (negative_matrix_max_size - len(ndoc_polarities)))
			for e in ndoc_polarities:
				neg_matrix_file.write(str(e) + ';')
			neg_matrix_file.write('\n')

		neg_matrix_file.close()

		pos_index_file = open('files_to_export/TripAdvisor/pos_index_file.txt','w+')
		neg_index_file = open('files_to_export/TripAdvisor/neg_index_file.txt','w+')

		for index in positive_matrix_index:
			pos_index_file.write(index)
			pos_index_file.write('\n')

		for index in negative_matrix_index:
			neg_index_file.write(index)
			neg_index_file.write('\n')

		pos_index_file.close()
		neg_index_file.close()

class CornellMoviesExport(BaseExport):
	"""docstring for CornellMoviesExport"""

	def __init__(self, cornell_movies_model):
		BaseExport.__init__(self, cornell_movies_model)

	def export_files(self):

		negative_matrix_polarities = []
		negative_matrix_max_size = 0.0
		positive_matrix_polarities = []
		positive_matrix_max_size = 0.0

		positive_matrix_index = []
		negative_matrix_index = []

		for ndoc in self.model.documents.find():

			adjectives = self.get_adjectives(ndoc)

			if ndoc['polarity'] == 0:
				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > negative_matrix_max_size:
					negative_matrix_max_size = len(ndoc_polarities)
				negative_matrix_polarities.append(ndoc_polarities)
				negative_matrix_index.append(ndoc['name'] + "-" + str(ndoc['_id']))

			elif ndoc['polarity'] == 1:
				ndoc_polarities = transformation.adjectives_polarities(adjectives) + \
										transformation.adv_adj_bigrams_polarities(ndoc['adv_adj_bigrams'])
				if len(ndoc_polarities) > positive_matrix_max_size:
					positive_matrix_max_size = len(ndoc_polarities)
				positive_matrix_polarities.append(ndoc_polarities)
				positive_matrix_index.append(ndoc['name'] + "-" + str(ndoc['_id']))

		pos_matrix_file = open('files_to_export/CornellMovies/pos_matrix_file.txt','w+')
		neg_matrix_file = open('files_to_export/CornellMovies/neg_matrix_file.txt','w+')

		for ndoc_polarity in positive_matrix_polarities:
			if positive_matrix_max_size - len(ndoc_polarity) > 0:
				ndoc_polarity = ndoc_polarity + ([0.0] * (positive_matrix_max_size - len(ndoc_polarity)))
			for e in ndoc_polarity:
				pos_matrix_file.write(str(e) + ';')
			pos_matrix_file.write('\n')

		pos_matrix_file.close()

		for ndoc_polarity in negative_matrix_polarities:
			if negative_matrix_max_size - len(ndoc_polarity) > 0:
				ndoc_polarity = ndoc_polarity + ([0.0] * (negative_matrix_max_size - len(ndoc_polarity)))
			for e in ndoc_polarity:
				neg_matrix_file.write(str(e) + ';')
			neg_matrix_file.write('\n')

		neg_matrix_file.close()

		pos_index_file = open('files_to_export/CornellMovies/pos_index_file.txt','w+')
		neg_index_file = open('files_to_export/CornellMovies/neg_index_file.txt','w+')

		for index in positive_matrix_index:
			pos_index_file.write(index)
			pos_index_file.write('\n')

		for index in negative_matrix_index:
			neg_index_file.write(index)
			neg_index_file.write('\n')

		pos_index_file.close()
		neg_index_file.close()
