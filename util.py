import math
from textblob import TextBlob, Word, Blobber
from textblob.taggers import PatternTagger, NLTKTagger
#Commented temporaly due to a bug after the upgrade to TextBlob 0.9
#from textblob_aptagger import PerceptronTagger

PENN_ADVERBS_TAGS = ['RB', 'RBR', 'RBS', 'RP']
PENN_ADJECTIVES_TAGS = ['JJ','JJR','JJS']
PENN_NOUNS_TAGS = ['NN','NNS','NNP','NNPS']
PENN_VERBS_TAGS = ['MD','VB','VBZ','VBP','VBD','VBN','VBG']
ALL_TAGS = PENN_ADVERBS_TAGS + PENN_ADJECTIVES_TAGS + PENN_NOUNS_TAGS + PENN_VERBS_TAGS
ADVERB_ADJECTIVE_BIGRAMS = ["RB/JJ","RB/JJR", "RB/JJS",
							"RBR/JJ","RBR/JJR", "RBR/JJS",
							"RBS/JJ","RBS/JJR", "RBS/JJS",
							"RP/JJ","RP/JJR", "RP/JJS"]
ADVERB_VERB_BIGRAMS = ['RB/MD','RB/VB','RB/VBZ','RB/VBP','RB/VBD','RB/VBN','RB/VBG',
						'RBR/MD','RBR/VB','RBR/VBZ','RBR/VBP','RBR/VBD','RBR/VBN','RBR/VBG',
						'RBS/MD','RBS/VB','RBS/VBZ','RBS/VBP','RBS/VBD','RBS/VBN','RBS/VBG',
						'RP/MD','RP/VB','RP/VBZ','RP/VBP','RP/VBD','RP/VBN','RP/VBG']

def get_list_bigrams(bigrams_list, bigrams_reference):
	"""Given a list of bigrams, this method return only those that are adv_adj_bigrams.

	Keyword arguments:
	bigrams_list -- list of bigrams in the following format - [(word1/tag1,word2/tag2)]
	bigrams_reference -- list of valid bigrams in the following format - ['Word/Tag']
	"""

	valids = []
	for bigram in bigrams_list:
		word1 = bigram[0]
		word2 = bigram[1]
		tags1 = word1.split('/')
		tags2 = word2.split('/')
		if len(tags1) > 1 and len(tags2) > 1:
			pattern = tags1[1] + "/" + tags2[1]
			if pattern in bigrams_reference:
				valids.append((word1.split('/')[0] + "/" + tags1[1],
								word2.split('/')[0] + "/" + tags2[1]))
	return valids

def get_list_trigrams(trigram_list, trigram_pattern):

	trigram_pattern_tags = trigram_pattern.split('/')
	first_word_tag = trigram_pattern_tags[0]
	second_word_tag = trigram_pattern_tags[1]
	third_word_tag = trigram_pattern_tags[2]

	if first_word_tag == "ADJ":
		first_word_pattern = PENN_ADJECTIVES_TAGS
	elif first_word_tag == "ADV":
		first_word_pattern = PENN_ADVERBS_TAGS
	elif first_word_tag == "NOUN":
		first_word_pattern = PENN_NOUNS_TAGS
	elif first_word_tag == "VERB":
		first_word_pattern = PENN_VERBS_TAGS
	else:
		first_word_pattern = ALL_TAGS

	if second_word_tag == "ADJ":
		second_word_pattern = PENN_ADJECTIVES_TAGS
	elif second_word_tag == "ADV":
		second_word_pattern = PENN_ADVERBS_TAGS
	elif second_word_tag == "NOUN":
		second_word_pattern = PENN_NOUNS_TAGS
	elif second_word_tag == "VERB":
		second_word_pattern = PENN_VERBS_TAGS
	else:
		second_word_pattern = ALL_TAGS

	if third_word_tag == "ADJ":
		third_word_pattern = PENN_ADJECTIVES_TAGS
	elif third_word_tag == "ADV":
		third_word_pattern = PENN_ADVERBS_TAGS
	elif third_word_tag == "NOUN":
		third_word_pattern = PENN_NOUNS_TAGS
	elif third_word_tag == "VERB":
		third_word_pattern = PENN_VERBS_TAGS
	else:
		third_word_pattern = ALL_TAGS

	valids = []
	for trigam in trigram_list:
		word1 = trigam[0]
		word2 = trigam[1]
		word3 = trigam[2]
		tags1 = word1.split('/')
		tags2 = word2.split('/')
		tags3 = word3.split('/')

		if len(tags1) > 1 and len(tags2) > 1 and len(tags3) > 1:
			if tags1[1] in first_word_pattern and tags2[1] in second_word_pattern \
				and tags3[1] in third_word_pattern:
				valids.append((word1.split('/')[0] + "/" + tags1[1],
								word2.split('/')[0] + "/" + tags2[1],
								word3.split('/')[0] + "/" + tags3[1]))
	return valids

def get_doc_adjectives(ndoc, bigrams_filtered=False, trigrams_filtered=False):
	"""This method return from document all the adjectives based on the following parameters:

	Keyword arguments:
	ndoc -- document from model
	bigrams_filtered -- Returns only adjectives that are not in ADV / ADJ bigrams (default: False)
	"""

	adjectives = list(ndoc['adjectives'])

	#TODO IF more bigrams are added, this list must be updated or a new one should be created
	#Or still it could be created a method in this module that gather all adjectives from the existed bigrams
	adjs_adv_adj_bigram = list(ndoc['adjs_adv_adj_bigram']) 

	#TODO IF more trigrams are added, this list must be updated or a new one should be created
	#Or still it could be created a method in this module that gather all adjectives from the existed trigrams
	try:
		trigrams = list(ndoc['adv_xxx_adj_trigrams'])
	except Exception, e:
		trigrams_filtered=False
	

	if bigrams_filtered:
		#removes from adjectives duplicates in adjs_adv_adj_bigram
		for e in adjs_adv_adj_bigram:
			if e in adjectives:
				adjectives.remove(e)

	if trigrams_filtered:
		#gathers adjectives from trigrams
		trigrams_adjectives = []
		for trigram in trigrams:
			for e in trigram:
				etag = e.split('/')[1]
				eword = e.split('/')[0]
				if etag in PENN_ADJECTIVES_TAGS:
					trigrams_adjectives.append(eword)

		for adj in adjs_adv_adj_bigram:
			if adj in trigrams_adjectives:
				trigrams_adjectives.remove(adj)

		#removes from adjectives duplicates in trigrams_adjectives
		for e in trigrams_adjectives:
			if e in adjectives:
				adjectives.remove(e)

	return adjectives

def get_doc_ngrams(ndoc,bigrams_types=['ADV/ADJ'], use_trigrams=True, filtered=True):

	unigrams = get_doc_adjectives(ndoc,filtered)
	bigrams = []
	trigrams = []

	one_trigram_list = []
	if use_trigrams:
		one_trigram_list = ndoc['adv_xxx_adj_trigrams']

	for p in bigrams_types:
		one_bigram_list_name = 'adv_adj_bigrams'
		if p == 'ADV/VERB':
			one_bigram_list_name = 'adv_verb_bigrams'

		one_bigram_list = ndoc[one_bigram_list_name]
		if filtered:
			for b in one_bigram_list:
				to_add = True
				for t in one_trigram_list:
					if b[0] == t[0] and b[1] == t[1]:
						to_add = False
					elif b[0] == t[1] and b[1] == t[2]:
						to_add = False
				if to_add:
					bigrams.append((b[0],b[1]))
		else:
			for b in one_bigram_list:
				bigrams.append((b[0],b[1]))

	for t in one_trigram_list:
		trigrams.append((t[0],t[1],t[2]))

	return unigrams + bigrams + trigrams

def average(list_of_numbers):
	return sum(list_of_numbers) * 1.0 / len(list_of_numbers)

def std(list_of_numbers):
	avg = average(list_of_numbers)
	variance = map(lambda x: (x - avg)**2, list_of_numbers)
	standard_deviation = math.sqrt(average(variance))
	return standard_deviation	

def tags(blob):

	parsed_text = blob.parse().split()
	tags = []	
	for parsed_sentence in parsed_text:
		for elem in parsed_sentence:
			tags.append((elem[0],elem[1]))

	return tags

def get_tagger(tagger="PerceptronTagger"):

	#Commented temporaly due to a bug after the upgrade to TextBlob 0.9
	#pt = Blobber(pos_tagger=PerceptronTagger())
	if tagger == "PatternTagger":
		pt = Blobber(pos_tagger=PatternTagger())
	else:
		pt = Blobber(pos_tagger=NLTKTagger())	

	return pt

def max_abs(list_of_numbers):
	max_abs_val = 0
	for num in list_of_numbers:
		if abs(num) > max_abs_val:
			max_abs_val = num
	return max_abs_val

def is_doc_positive(doc):
	is_positive = False

	if ('polarity' in doc.keys() and doc['polarity'] == 1) or ('degree' in doc.keys() and int(doc['degree']) >= 4):
		is_positive = True

	return is_positive

def normalize_number(number, lower, upper, _round=False):
	normalized = (float(number) - lower) / (upper - lower)
	return round(normalized,2) if _round else normalized

def normalize_list(list_of_numbers, lower=None, upper=None):
	_min = float(min(list_of_numbers)) if lower is None else lower
	_max = float(max(list_of_numbers)) if upper is None else upper
	normalized_list = []
	
	for num in list_of_numbers:
		normalized_list.append(normalize_number(num, _min, _max))
	return normalized_list
					
