import pre_processing as pp
import transformation as trans
import os

corpora_path = '/corpora/cs_cornell_edu/txt_sentoken/'
positive_document = corpora_path + '/pos/cv491_12145.txt'
negative_document = corpora_path + '/neg/cv200_29006.txt'

# print os.getcwd()
# print os.path.basename(__file__)
# print os.path.abspath(__file__)
# print os.path.dirname(__file__)

file_path = os.getcwd() + negative_document

raw_text = open(file_path).read()
#pre_processing
raw_text_no_punctuation = pp.punctuation_removal(raw_text)
tokens = pp.tokenizer(raw_text_no_punctuation)
tokens_no_stopwords = pp.stopwords_removal(tokens)
tuples = pp.pos_tagger(tokens_no_stopwords)
tuples_JJ = [t for t in tuples if t[1] == "JJ"]

#transformation and classification
num_JJ = 0
sum_JJ_polarity = 0
for JJ in tuples_JJ:
	word_synset = trans.word_polarity(JJ[0])
	if len(word_synset) > 0:
		num_JJ = num_JJ + 1
		print JJ[0], JJ[1], word_synset[0].weight
		sum_JJ_polarity = sum_JJ_polarity + word_synset[0].weight[0]

print sum_JJ_polarity
print sum_JJ_polarity / num_JJ
