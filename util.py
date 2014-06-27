def get_bigrams(bigrams_list, bigrams_reference):
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
