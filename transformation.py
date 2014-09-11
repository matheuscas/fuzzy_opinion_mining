import math
import util
from pattern.en import wordnet
from pattern.en import NOUN, VERB, ADJECTIVE, ADVERB
from textblob import Word
from lexicons import SentiWords

__sentiwords = SentiWords()

ATTENUATORS_ADVERBS = open('groups_of_adverbs/medium_attenuator_adv.txt','r').readlines()
ATTENUATORS_ADVERBS = ATTENUATORS_ADVERBS + open('groups_of_adverbs/strong_attenuator_adv.txt','r').readlines()
ATTENUATORS_ADVERBS = ATTENUATORS_ADVERBS + open('groups_of_adverbs/weak_attenuator_adv.txt','r').readlines()

INTENSIFIERS_ADVERBS = open('groups_of_adverbs/medium_intensifier_adv.txt','r').readlines()
INTENSIFIERS_ADVERBS = INTENSIFIERS_ADVERBS + open('groups_of_adverbs/strong_intensifier_adv.txt','r').readlines()
INTENSIFIERS_ADVERBS = INTENSIFIERS_ADVERBS + open('groups_of_adverbs/weak_intensifier_adv.txt','r').readlines()

NON_GRADING_ADVERBS = open('groups_of_adverbs/non_grading_adv.txt','r').readlines()

def word_polarity(word, pos_tag=None, prior_polarity_score=False):
	"""returns a (polarity, subjectivity)-tuple for the given word from SENTIWORDNET.
	If there is no synsets for the given word, None will be returned
	The word can be NOUN, VERB, ADJECTIVE, ADVERB"""

	if prior_polarity_score:
		return __word_prior_polarity(word, pos_tag)

	pos_tag = "NOUN" if pos_tag in util.PENN_NOUNS_TAGS else pos_tag
	pos_tag = "VERB" if pos_tag in util.PENN_VERBS_TAGS else pos_tag
	pos_tag = "ADVERB" if pos_tag in util.PENN_ADVERBS_TAGS else pos_tag
	pos_tag = "ADJECTIVE" if pos_tag in util.PENN_ADJECTIVES_TAGS else None

	TAGS = {"NOUN":NOUN, "VERB":VERB, "ADJECTIVE":ADJECTIVE, "ADVERB":ADVERB}
	TAG = TAGS[pos_tag] if pos_tag else ADJECTIVE

	synsets = wordnet.synsets(word, TAG)
	if len(synsets) > 0:
		return synsets[0].weight
	else:
		return None

def __word_prior_polarity(word, pos_tag=None):

	pos_tag = "n" if pos_tag in util.PENN_NOUNS_TAGS else pos_tag
	pos_tag = "v" if pos_tag in util.PENN_VERBS_TAGS else pos_tag
	pos_tag = "r" if pos_tag in util.PENN_ADVERBS_TAGS else pos_tag
	pos_tag = "a" if pos_tag in util.PENN_ADJECTIVES_TAGS else None

	if pos_tag is None:
		pos_tag = 'a'

	prior_polarity_score = __sentiwords.get_entry_by_name_and_pos(word,pos_tag)
	if prior_polarity_score is None:
		return None
	return (prior_polarity_score['prior_polarity_score'], 0)	

def is_negation(bigram_first_word):
	"""Gets the fist word of a bigram and checks if this words is a negation or contraction word"""

	NEGATION_WORDS = ['no','not']
	NEGATION_CONTRACTIONS = ["isn't","aren't","wasn't","weren't","haven't",
								"hasn't","hadn't","won't","wouldn't","don't",
								"doesn't","didn't","can't","couldn't","shouldn't"
								"mightn't","mustn't","ain't","mayn't","oughtn't",
								"shan't"]

	return (bigram_first_word in NEGATION_WORDS) or (bigram_first_word in NEGATION_CONTRACTIONS)

def invert_polarity(polarity, type=None):
	"""It inverts or do a complement of the polarity"""

	if type == 'complement':
		if polarity < 0:
			return -(1.0 - abs(polarity))
		else:
			return 1.0 - polarity

	return -1.0 * polarity

def apply_adverb_factor(adverb, polarity, negation=None):

	if is_negation(adverb):
		return invert_polarity(polarity, negation)

	bigram_polarity = 0.0
	type = 1 #non-grading again
	polarity = float(polarity)

	factor = 1.0 #assumes that is non_grading by default
	for att_adv in ATTENUATORS_ADVERBS:
		if adverb in att_adv:
			values = att_adv.split('\n')[0]
			values = values.split(';')
			factor = float(values[1])
			type = 2
			break

	if factor == 1.0: #did not find nothing in attenuators
		for int_adv in INTENSIFIERS_ADVERBS:
			if adverb in int_adv:
				values = int_adv.split('\n')[0]
				values = values.split(';')
				factor = float(values[1])
				type = 3
				break

	if type == 3:
		if polarity < 0:
			#print 'adverb + polarity: ' + str(- math.pow(abs(polarity), 1.0 / factor))
			return (- math.pow(abs(polarity), 1.0 / factor))
		else:
			#print 'adverb + polarity: ' + str(math.pow(polarity, 1.0 / factor))
			return (math.pow(polarity, 1.0 / factor))
	elif type == 2:
		if polarity < 0:
			#print 'adverb + polarity: ' + str(- math.pow(abs(polarity), factor))
			return (- math.pow(abs(polarity), factor))
		else:
			#print 'adverb + polarity: ' + str(math.pow(polarity,factor))
			return (math.pow(polarity,factor))
	elif type == 1:
		return polarity


def default_adv_xxx_bigram_polarity(bigram, negation=None, prior_polarity_score=False):
	"""Calculates the bigram polarity based on a empirical factor from each adverb group
		and SENTIWORDNET word polarity
	"""

	adverb = bigram[0].split('/')[0]
	adverb_tag = bigram[0].split('/')[1]

	ngram_2 = bigram[1].split('/')[0]
	ngram_2_tag = bigram[1].split('/')[1]

	ngram_2_polarity = word_polarity(ngram_2, ngram_2_tag, prior_polarity_score=prior_polarity_score)

	# If is a verb, tries again in lemmatized form
	if ngram_2_tag in util.PENN_VERBS_TAGS and \
		(ngram_2_polarity == None or ngram_2_polarity[0] == 0):
			w = Word(ngram_2)
			ngram_2_polarity = word_polarity(w.lemmatize("v"), prior_polarity_score=prior_polarity_score)

	#if the ngram_2 does not have polarity, so stops the method
	if ngram_2_polarity == None:
		return None

	return apply_adverb_factor(adverb,ngram_2_polarity[0], negation)


def adjectives_polarities(list_of_adjectives, prior_polarity_score=False):
	"""This method calculates all adjectives polarities based on the following arguments

	Keyword arguments:
	list_of_adjectives -- list of adjectives from a document
	"""

	adjectives_polarities = []
	for adjective in list_of_adjectives:
		polarity = word_polarity(adjective, prior_polarity_score=prior_polarity_score)
		if polarity and polarity[0] != 0.0:
			adjectives_polarities.append(polarity[0])

	return adjectives_polarities

def adv_adj_bigrams_polarities(list_of_adv_adj_bigrams, negation=None, prior_polarity_score=False):
	"""This method calculates all bigrams polarities based on the following arguments

	Keyword arguments:
	list_of_adv_adj_bigrams -- list of bigrams in the following format: ADVERB / ADJECTIVE
	"""

	adv_adj_bigrams_polarities = []
	for bigram in list_of_adv_adj_bigrams:
		bigram_polarity = default_adv_xxx_bigram_polarity(bigram, negation, prior_polarity_score=prior_polarity_score)
		if bigram_polarity:
			adv_adj_bigrams_polarities.append(bigram_polarity)

	return adv_adj_bigrams_polarities

def trigram_polarity(trigram, negation=None, prior_polarity_score=False):
	first_word = trigram[0]
	middle_word = trigram[1]
	third_word = trigram[2]

	#words
	first_word_word = first_word.split('/')[0]

	#word tags
	middle_word_tag = middle_word.split('/')[1]
	third_word_tag = third_word.split('/')[1]

	results = []
	#adv/adv/adj trigram
	if middle_word_tag in util.PENN_ADVERBS_TAGS and third_word_tag in util.PENN_ADJECTIVES_TAGS:
		parcial_result = default_adv_xxx_bigram_polarity((middle_word,third_word), negation, prior_polarity_score=prior_polarity_score)
		if parcial_result == None:
			return None
		parcial_result = apply_adverb_factor(first_word_word,parcial_result)
		if parcial_result != None and abs(parcial_result) != 0:
			results.append(parcial_result)
		return results
	#adv/verb/adj or #adv/adj/adj trigram
	# elif middle_word_tag in util.PENN_ADJECTIVES_TAGS or \
	# 		middle_word_tag in util.PENN_VERBS_TAGS:
	# 		parcial_result = default_adv_xxx_bigram_polarity((first_word,middle_word), negation)
	# 		if parcial_result != None and abs(parcial_result) != 0:
	# 			results.append(parcial_result)

	# 		parcial_result_2 = word_polarity(third_word.split('/')[0])
	# 		if parcial_result_2 != None and abs(parcial_result_2[0]) != 0:
	# 			results.append(parcial_result_2[0])
	# 		return results

	return results

def ngrams_polarities(ngrams_list, negation=None, prior_polarity_score=False):
	"""
		Given a list of ngrams (such as "good, bad, (very,good),awesome"), returns a list of corresponding polarities
	"""

	polarities = []
	for ngram in ngrams_list:
		pol = 0

		if type(ngram) is tuple and len(ngram) == 2: #bigrams - adverbs and adjectives
			pol = default_adv_xxx_bigram_polarity(ngram, negation, prior_polarity_score=prior_polarity_score)
		elif type(ngram) is tuple and len(ngram) == 3: #trigrams - adverbs xxx adjectives
			pols = trigram_polarity(ngram, negation, prior_polarity_score=prior_polarity_score)
			if pols != None:
				polarities = polarities + pols
		else: #unigrams - adjectives
			pol = word_polarity(ngram, prior_polarity_score=prior_polarity_score)
		if pol != None and type(pol) is tuple and pol[0] != 0:
			polarities.append(pol[0])
		elif pol != None and (type(pol) is int or type(pol) is float) and pol != 0:
			polarities.append(pol)

	return polarities

def ngrams_matrix_polarities(ngrams_matrix, negation=None, prior_polarity_score=False):
	"""Given a matrix of ngrams (or a list of ngrams list), return a matrix of its corresponding polarities"""

	polarities_matrix = {}
	for _id, ngrams_list in ngrams_matrix.iteritems():
		polarities_matrix[_id] = ngrams_polarities(ngrams_list, negation, prior_polarity_score=prior_polarity_score)

	return polarities_matrix		
