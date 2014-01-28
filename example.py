import os
import domain
import classification
import pre_processing as pp
import transformation as trans
import evaluation as eval
import decimal

adjectives = ['JJ']
adjectives_adverbs = ['JJ','RB']
adjectives_verbs = ['JJ','VB','VBZ','VBP']
adjectives_adverbs_verbs = ['JJ','VB','VBZ','VBP', 'RB']

extract=adjectives_adverbs_verbs

print extract

path = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/'
corpora = domain.Cornell(path)
corpora.create_documents_list()
all_documents = corpora.all_documents_list()

# part_of_pos = all_documents[:10]
# part_of_neg = all_documents[1990:]
# all_documents = part_of_pos + part_of_neg


classifier = classification.Classification(all_documents, extract=extract)
classifier.term_counting()
print str(eval.precision(len(corpora.positives), all_documents[1000:]) * decimal.Decimal(100)) + ' %'
print str(eval.recall(len(corpora.positives), corpora.positives) * decimal.Decimal(100)) + ' %'
print str(eval.accuracy(len(corpora.positives), len(corpora.negatives), all_documents) * decimal.Decimal(100)) + ' %'

