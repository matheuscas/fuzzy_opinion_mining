import math
from pattern.en import wordnet
from pattern.en import NOUN, VERB, ADJECTIVE, ADVERB

ATTENUATORS_ADVERBS = open('groups_of_adverbs/medium_attenuator_adv.txt','r').readlines()
ATTENUATORS_ADVERBS = ATTENUATORS_ADVERBS + open('groups_of_adverbs/strong_attenuator_adv.txt','r').readlines()
ATTENUATORS_ADVERBS = ATTENUATORS_ADVERBS + open('groups_of_adverbs/weak_attenuator_adv.txt','r').readlines()

INTENSIFIERS_ADVERBS = open('groups_of_adverbs/medium_intensifier_adv.txt','r').readlines()
INTENSIFIERS_ADVERBS = INTENSIFIERS_ADVERBS + open('groups_of_adverbs/strong_intensifier_adv.txt','r').readlines()
INTENSIFIERS_ADVERBS = INTENSIFIERS_ADVERBS + open('groups_of_adverbs/weak_intensifier_adv.txt','r').readlines()

NON_GRADING_ADVERBS = open('groups_of_adverbs/non_grading_adv.txt','r').readlines()

def word_polarity(word, pos_tag=None):
	"""returns a (polarity, subjectivity)-tuple for the given word from SENTIWORDNET.
	If there is no synsets for the given word, None will be returned
	The word can be NOUN, VERB, ADJECTIVE, ADVERB"""

	TAGS = {"NOUN":NOUN, "VERB":VERB, "ADJECTIVE":ADJECTIVE, "ADVERB":ADVERB}
	TAG = TAGS[pos_tag] if pos_tag else ADJECTIVE

	synsets = wordnet.synsets(word, TAG)
	if len(synsets) > 0:
		return synsets[0].weight
	else:
		return None

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
	"""It Inverts polarity"""

	if type == 'complement':
		if polarity < 0:
			return -(1.0 - abs(polarity))
		else:
			return 1.0 - polarity

	return -1.0 * polarity

def default_adv_adj_bigram_polarity(bigram):
	adverb = bigram[0].split('/')[0]
	adverb_tag = bigram[0].split('/')[1]

	adjective = bigram[1].split('/')[0]
	adjective_tag = bigram[1].split('/')[1]

	adjective_polarity = word_polarity(adjective)

	#if the adjective does not have polarity, so stops the method
	if adjective_polarity == None:
		return None

	if is_negation(adverb):
		return invert_polarity(adjective_polarity[0])

	bigram_polarity = 0.0
	type = 1 #non-grading again
	adjective_polarity = float(adjective_polarity[0])

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
		if adjective_polarity < 0:
			#print 'adverb + adjective_polarity: ' + str(- math.pow(abs(adjective_polarity), 1.0 / factor))
			return (- math.pow(abs(adjective_polarity), 1.0 / factor))
		else:
			#print 'adverb + adjective_polarity: ' + str(math.pow(adjective_polarity, 1.0 / factor))
			return (math.pow(adjective_polarity, 1.0 / factor))
	elif type == 2:
		if adjective_polarity < 0:
			#print 'adverb + adjective_polarity: ' + str(- math.pow(abs(adjective_polarity), factor))
			return (- math.pow(abs(adjective_polarity), factor))
		else:
			#print 'adverb + adjective_polarity: ' + str(math.pow(adjective_polarity,factor))
			return (math.pow(adjective_polarity,factor))
	elif type == 1:
		return adjective_polarity




