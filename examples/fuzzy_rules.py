import os
import decimal
import sys
import argparse

sys.path.insert(1, os.path.join(sys.path[0], '..'))

print 'Building stopwords list'

import domain
import pre_processing as pp
import transformation as trans
import evaluation as eval

ADVS = ['RB','RBR','RBS']
ADJS = ['JJ','JJR','JJS']

PENN_TAGS_TO_SENTIWORDNET_TAGS = {'JJ':'ADJECTIVE',
									'JJR':'ADJECTIVE',
									'JJS':'ADJECTIVE',
									'RB':'ADVERB',
									'RBR':'ADVERB',
									'RBS':'ADVERB',
									'VB':'VERB',
									'VBZ':'VERB',
									'VBP':'VERB'}


def extract_words(bigram):
	return (bigram[0].split('/')[0], bigram[1].split('/')[0])

def extract_tags(bigram):
	return (bigram[0].split('/')[1], bigram[1].split('/')[1])

def is_valid_bigram(bigram):
	part1 = bigram[0]

	if not '/' in part1:
		return False

	part1_subparts = part1.split('/')

	if not len(part1_subparts) > 1:
		return False

	if not len(part1_subparts[0]) > 0:
		return False

	if not len(part1_subparts[1]) > 0:
		return False

	part2 = bigram[1]

	if not '/' in part2:
		return False

	part2_subparts = part2.split('/')

	if not len(part2_subparts) > 1:
		return False

	if not len(part2_subparts[0]) > 0:
		return False

	if not len(part2_subparts[1]) > 0:
		return False

	return True

FACTOR = 0.35
#Adaptacao do APS (Adjective Priority Score) 0.35 de Benamara
def aps_035(bigram):

	words = extract_words(bigram)
	tags = extract_tags(bigram)
	adj_degree = trans.word_polarity(words[1],PENN_TAGS_TO_SENTIWORDNET_TAGS[tags[1]])
	adv_degree = trans.word_polarity(words[0],PENN_TAGS_TO_SENTIWORDNET_TAGS[tags[0]])

	if adv_degree is None or adv_degree[0] == 0:
		if adj_degree is not None:
			return adj_degree[0]
		else:
			return None
	elif adj_degree is None:
		return None
	elif adv_degree[0] > 0 and adj_degree[0] < 0:
		return float(adj_degree[0]) - (FACTOR * float(adv_degree[0])) #ADV > 0 E ADJ < 0 - adjetivo que
	elif adv_degree[0] > 0 and adj_degree[0] > 0:
		return float(adj_degree[0]) + (FACTOR * float(adv_degree[0])) #ADV > 0 E ADJ > 0
	elif adv_degree[0] < 0 and adj_degree[0] > 0:
		return float(adj_degree[0]) + (FACTOR * float(adv_degree[0])) #ADV < 0 E ADJ > 0
	elif adv_degree[0] < 0 and adj_degree[0] < 0:
		return float(adj_degree[0]) + (FACTOR * float(adv_degree[0])) #ADV < 0 E ADJ < 0
	else:
		return 0

def is_adv_adj(bigram):
	bigram_part_1 = bigram[0]
	bigram_part_2 = bigram[1]

	print bigram
	if not is_valid_bigram(bigram):
		return False

	if bigram_part_1.split('/')[1] in ADVS and bigram_part_2.split('/')[1] in ADJS:
		return True

	return False

def is_negation(bigram):
	"""Checks if comes a not or never before a adjective"""

	negation_words = ['not','never']

	bigram_part_1 = bigram[0]
	bigram_part_2 = bigram[1]

	if bigram_part_1.split('/')[0] in negation_words:
		return True

	return False

def calc_negation(bigram):

	words = extract_words(bigram)
	tags = extract_tags(bigram)
	adj_degree = trans.word_polarity(words[1],PENN_TAGS_TO_SENTIWORDNET_TAGS[tags[1]])
	if adj_degree is None:
		return None
	return adj_degree[0] * (-1)

def peanut_classification(degrees):
	sum = float(0)
	for degree in degrees:
		sum += float(degree)
	return sum

print "creating documents"
path = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/'
corpora = domain.Cornell(path)
corpora.create_documents_list()

how_many = 1000
doc_count = 1

print 'Extracting sentences from positive documents'
for document in corpora.positives[:how_many]:
	print str(doc_count) + "/" + str(how_many)
	document.sentences = document.raw_text.split('\n')
	bigrams_list = []
	for s in document.sentences:
		temp_bigrams = pp.pattern_pos_tag_and_remove_sw(s,ngrams=pp.BIGRAMS)
		for t in temp_bigrams:
			if not is_valid_bigram(t):
				temp_bigrams.remove(t)
		bigrams_list.append(temp_bigrams)

	document.bigrams = bigrams_list
	doc_count += 1

doc_count = 1
print 'Extracting sentences from negative documents'
for document in corpora.negatives[:how_many]:
	print str(doc_count) + "/" + str(how_many)
	document.sentences = document.raw_text.split('\n')
	bigrams_list = []
	for s in document.sentences:
		temp_bigrams = pp.pattern_pos_tag_and_remove_sw(s,ngrams=pp.BIGRAMS)
		for t in temp_bigrams:
			if not is_valid_bigram(t):
				temp_bigrams.remove(t)
		bigrams_list.append(temp_bigrams)
	document.bigrams = bigrams_list
	doc_count += 1

doc_count = 1
print 'Transforming positive bigrams'
for document in corpora.positives[:how_many]:
	print str(doc_count) + "/" + str(how_many)
	degrees = []
	for bigrams_list in document.bigrams:
		for bigram in bigrams_list:
			if is_adv_adj(bigram) and is_negation(bigram):
				degree = calc_negation(bigram)
				if degree is not None:
					degrees.append(degree)
			elif is_adv_adj(bigram) and not is_negation(bigram):
				degree = aps_035(bigram)
				if degree is not None:
					degrees.append(degree)
	document.degrees = degrees
	doc_count += 1

doc_count = 1
print 'Transforming negative bigrams'
for document in corpora.negatives[:how_many]:
	print str(doc_count) + "/" + str(how_many)
	degrees = []
	for bigrams_list in document.bigrams:
		for bigram in bigrams_list:
			if is_adv_adj(bigram) and is_negation(bigram):
				degree = calc_negation(bigram)
				if degree is not None:
					degrees.append(degree)
			elif is_adv_adj(bigram) and not is_negation(bigram):
				degree = aps_035(bigram)
				if degree is not None:
					degrees.append(degree)
	document.degrees = degrees
	doc_count += 1


print 'classication of positive documents'
for document in corpora.positives[:how_many]:
	document.predicted_polarity = peanut_classification(document.degrees)

print 'classication of negative documents'
for document in corpora.negatives[:how_many]:
	document.predicted_polarity = peanut_classification(document.degrees)

print
print 'Precision: ' + str(eval.precision(how_many,corpora.negatives[:how_many]))
print 'Recall: ' + str(eval.recall(how_many, corpora.positives[:how_many]))
print 'Accuracy: ' + str(eval.accuracy(how_many,how_many, corpora.negatives[:how_many] + corpora.positives[:how_many]))


