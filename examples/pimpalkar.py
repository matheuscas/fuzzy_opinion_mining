import os
import decimal
import sys
import argparse

sys.path.insert(1, os.path.join(sys.path[0], '..'))

import domain
import classification
import pre_processing as pp
import evaluation as eval

parser = argparse.ArgumentParser()
parser.add_argument("qDocs", action="store", help="number of documents to be analyzes and classified", type=int)
parser.add_argument("-sw","--stopwords", help="stopwords are stripped off",action="store_true")

args = parser.parse_args()

clear = lambda: os.system('clear')

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
	pp.extract_ngrams(p_doc[1], stopwords=args.stopwords)
	clear()

for n_doc in list(enumerate(corpora.negatives[:num_of_documents])):
	print "extracting ngrams from negative documents"
	print n_doc[0]
	pp.extract_ngrams(n_doc[1], stopwords=args.stopwords)
	clear()

print "____________________CLASSIFICATION STAGE____________________"
all_documents = corpora.positives[:num_of_documents] + corpora.negatives[:num_of_documents]
classifier = classification.Pimpalkar(all_documents)
classifier.opinion_analyzer()

print "____________________EVALUATION STAGE____________________"
print args
print
print "Some documents couldn't be predicted, then they was assigned with None and will not be evaluated"
positive_docs_non_predicted = 0
list_of_true_negative_documents = []
for tn in corpora.negatives[:num_of_documents]:
	if tn.predicted_polarity:
		list_of_true_negative_documents.append(tn)
	else:
		positive_docs_non_predicted += 1

negative_docs_non_predicted = 0
list_of_true_positive_documents = []
for tp in corpora.positives[:num_of_documents]:
	if tp.predicted_polarity:
		list_of_true_positive_documents.append(tp)
	else:
		negative_docs_non_predicted += 1

print "Positive docs non predicted: " + str(positive_docs_non_predicted)
print "Negative docs non predicted: " + str(negative_docs_non_predicted)
print

print "Precision"
print str(eval.precision(len(corpora.positives[:num_of_documents]), list_of_true_negative_documents, ref=0.5) * decimal.Decimal(100)) + ' %'
print "Recall"
print str(eval.recall(len(corpora.positives[:num_of_documents]), list_of_true_positive_documents, ref=0.5) * decimal.Decimal(100)) + ' %'
print "Accuracy"
print str(eval.accuracy(len(corpora.positives), len(corpora.negatives),
				list_of_true_positive_documents + list_of_true_negative_documents, ref=0.5) * decimal.Decimal(100)) + ' %'

