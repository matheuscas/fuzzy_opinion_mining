"""THIS WILL BE DEPRECATED"""

import model
import transformation as tf
import math

mongo_client = model.get_mongo_client()
documents = mongo_client['cornell']['documents'].find()
p_adj = mongo_client['cornell']['p_adj']

"""
Para cada documento eu tenho que:
pegar todos os adjetivos (unigrams) do documento e cuidarp ara nao repetir com os adjetivos dos bigrams
pegar todos os bigrams do documento
calcular a polaridade de todos os unigrams
calcular a polaridade de todos os bigrams

Depois exportar isso num formato que o matlab possa ler
"""

max_pos = 0
max_neg = 0
pos_matrix = []
neg_matrix = []

pos_matrix_file_index = open('files_to_export/pos_matrix_file_index.txt','w+')
neg_matrix_file_index = open('files_to_export/neg_matrix_file_index.txt','w+')

count = 1
for doc in documents:

	print str(count) + ' de ' + '2000'
	#get unigrams and remove duplicated adjectives between bigrams and unigrams
	unigrams = doc['adjectives']
	bigram_adjs = doc['ngrams_adjectives']
	for e in bigram_adjs:
		if e in unigrams:
			unigrams.remove(e)

	#calculates unigrams polarities
	unigrams_polarities = []
	for unigram in unigrams:
		polarity = tf.word_polarity(unigram)
		if polarity and polarity[0] != 0.0:
			unigrams_polarities.append(polarity[0])

	verbs = doc['verbs']
	for verb in verbs:
		polarity = tf.word_polarity(verb, pos_tag="VERB")
		if polarity and polarity[0] != 0.0:
			unigrams_polarities.append(polarity[0])

	nouns = doc['nouns']
	for noun in nouns:
		polarity = tf.word_polarity(noun, pos_tag="NOUN")
		if polarity and polarity[0] != 0.0:
			unigrams_polarities.append(polarity[0])

	#get bigrams
	bigrams = doc['bigrams']

	#calculates bigrams polarities
	bigrams_polarities = []
	for bigram in bigrams:
		word1 = bigram[0].split('/')[0]
		word1_tag = bigram[0].split('/')[1]

		word2 = bigram[1].split('/')[0]
		word2_tag = bigram[1].split('/')[1]

		#print '------------------------------'
		#print adverb, adjective

		adj_polarity = None
		adj_polarity = tf.word_polarity(word2)
		#word_found = p_adj.find_one({"word":word2})
		#if word_found:
		#	adj_polarity = [word_found['p_polarity']]

		bigram_polarity = 0 #not calculated yet

		#if is not non-grading nor intensifier nor attenuator
		factor = 0.0
		# 0 neither types; 1 is non-grading; 2 is attenuators; 3 is intensifier
		type = 0

		for w in mongo_client['cornell']['intensifiers_adv'].find({"word": word1}):
			factor = float(w['factor'])
			type = 3
			#print 'intensifier adverb'

		for w in mongo_client['cornell']['attenuators_adv'].find({"word": word1}):
			factor = float(w['factor'])
			type = 2
			#print 'attenuator adverb'

		for w in mongo_client['cornell']['non_grading_adv'].find({"word": word1}):
			factor = 1
			type = 1
			#print 'non_grading adverb'

		is_negation = tf.is_negation(word1)
		if adj_polarity and adj_polarity[0] and factor and type and not is_negation:
			#print 'adj_polarity[0]: ' + str(adj_polarity[0])
			if type == 3:
				if adj_polarity[0] < 0:
					#print 'adverb + adj_polarity[0]: ' + str(- math.pow(abs(adj_polarity[0]), 1.0 / factor))
					bigrams_polarities.append(- math.pow(abs(adj_polarity[0]), 1.0 / factor))
				else:
					#print 'adverb + adj_polarity[0]: ' + str(math.pow(adj_polarity[0], 1.0 / factor))
					bigrams_polarities.append(math.pow(adj_polarity[0], 1.0 / factor))
			elif type == 2:
				if adj_polarity[0] < 0:
					#print 'adverb + adj_polarity[0]: ' + str(- math.pow(abs(adj_polarity[0]), factor))
					bigrams_polarities.append(- math.pow(abs(adj_polarity[0]), factor))
				else:
					#print 'adverb + adj_polarity[0]: ' + str(math.pow(adj_polarity[0],factor))
					bigrams_polarities.append(math.pow(adj_polarity[0],factor))
			elif type == 1:
				bigrams_polarities.append(adj_polarity[0])
		elif adj_polarity and adj_polarity[0] and factor and type and is_negation:
			bigrams_polarities.append(tf.invert_polarity(adj_polarity[0],type='complement'))


	#print  unigrams_polarities + bigrams_polarities
	#print
	#print '##########################################'

	ngrams_polarities = unigrams_polarities + bigrams_polarities
	size_polarities = len(ngrams_polarities)
	if size_polarities > max_pos and doc['polarity'] == 1:
		max_pos = size_polarities
	elif size_polarities > max_neg and doc['polarity'] == 0:
		max_neg = size_polarities

	if doc['polarity'] == 1:
		pos_matrix.append(ngrams_polarities)
		pos_matrix_file_index.write(doc['name'] + '\n')
	else:
		neg_matrix.append(ngrams_polarities)
		neg_matrix_file_index.write(doc['name'] + '\n')

	count = count + 1

pos_matrix_file_index.close()
neg_matrix_file_index.close()

pos_matrix_file = open('files_to_export/pos_matrix_file.txt','w+')
neg_matrix_file = open('files_to_export/neg_matrix_file.txt','w+')

print 'writing on files'

for list in pos_matrix:
	if max_pos - len(list) > 0:
		list = list + ([0.0] * (max_pos - len(list)))
	for e in list:
		pos_matrix_file.write(str(e) + ';')
	pos_matrix_file.write('\n')

pos_matrix_file.close()

for list in neg_matrix:
	if max_neg - len(list) > 0:
		list = list + ([0.0] * (max_neg - len(list)))
	for e in list:
		neg_matrix_file.write(str(e) + ';')
	neg_matrix_file.write('\n')

neg_matrix_file	.close()

