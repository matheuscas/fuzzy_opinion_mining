import os
import domain
import classification
import pre_processing as pp
import transformation as trans
import evaluation as eval
import decimal
import time
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("qDocs", action="store", help="number of documents to be analyzes and classified", type=int)
parser.add_argument('-tags', action='append', default=['JJ'],help='Tags to be analyzed. RB for adverbs; \
	VB, VBZ and VPB for verbs. JJ for adjectives is already default')

args = parser.parse_args()

# adjectives = ['JJ']
# adjectives_adverbs = ['JJ','RB']
# adjectives_verbs = ['JJ','VB','VBZ','VBP']
# adjectives_adverbs_verbs = ['JJ','VB','VBZ','VBP', 'RB']

clear = lambda: os.system('clear')

print args.tags
print "____________________PRE-PROCESSING STAGE____________________"
print "creating documents"
path = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/'
corpora = domain.Cornell(path)
corpora.create_documents_list()

# num_of_documents = len(corpora.positives) + len(corpora.negatives)
num_of_documents = args.qDocs

for p_doc in list(enumerate(corpora.positives[:num_of_documents])):
	print "extracting ngrams from positive documents"
	print p_doc[0]
	pp.extract_ngrams(p_doc[1])
	clear()

for n_doc in list(enumerate(corpora.negatives[:num_of_documents])):
	print "extracting ngrams from negative documents"
	print n_doc[0]
	pp.extract_ngrams(n_doc[1])
	clear()

print "____________________CLASSIFICATION STAGE____________________"
all_documents = corpora.positives[:num_of_documents] + corpora.negatives[:num_of_documents]
classifier = classification.OhanaBrendan(all_documents)
classifier.rule = args.tags
classifier.term_counting()

print "____________________EVALUATION STAGE____________________"

print "Precision"
print str(eval.precision(len(corpora.positives[:num_of_documents]), corpora.negatives[:num_of_documents]) * decimal.Decimal(100)) + ' %'
print "Recall"
print str(eval.recall(len(corpora.positives[:num_of_documents]), corpora.positives[:num_of_documents]) * decimal.Decimal(100)) + ' %'
print "Accuracy"
print str(eval.accuracy(len(corpora.positives), len(corpora.negatives), all_documents) * decimal.Decimal(100)) + ' %'

