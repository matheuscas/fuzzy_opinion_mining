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

def get_ndoc_adjectives(ndoc, filtered=True):
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

def get_doc_ngrams(ndoc,bigrams_types=['ADV/ADV'],filtered=True):
	unigrams = get_ndoc_adjectives(ndoc,filtered)
	bigrams = []
	for p in bigrams_types:
		one_bigram_list_name = 'adv_adj_bigrams'
		if p == 'ADV/VERB':
			one_bigram_list_name = 'adv_verb_bigrams'

		one_bigram_list = ndoc[one_bigram_list_name]
		if filtered:
			adv_xxx_adj = ndoc['adv_xxx_adj_trigrams']
			for t in adv_xxx_adj:
				for b in one_bigram_list:
					to_add = True
					if b[0] == t[0] and b[1] == t[1]:
						to_add = False
					elif b[0] == t[1] and b[1] == t[2]:
						to_add = False
					if to_add and (b[0],b[1]) not in bigrams:
						bigrams.append((b[0],b[1]))
		else:
			for b in one_bigram_list:
				bigrams.append((b[0],b[1]))

	trigrams = []
	one_trigram_list = ndoc['adv_xxx_adj_trigrams']
	for t in one_trigram_list:
		trigrams.append((t[0],t[1],t[2]))

	return unigrams + bigrams + trigrams
