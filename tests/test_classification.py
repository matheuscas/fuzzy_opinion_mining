import os
import sys
import string
from pattern.en import ngrams, parse, tag

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from classification import OhanaBrendan
from domain import Document

document_sample_text = "both those films were tense exercises in chills ."

""" (u'both/DT',), (u'those/DT',), (u'films/NNS',), (u'were/VBD',), (u'tense/JJ',),
	(u'exercises/NNS',), (u'in/IN',), (u'chills/NNS',), (u'./',)] """

def test_OhanaBrendan_extract_pos_tagged_element():

	doc = Document('sample', document_sample_text, 0)

	tagged = parse(doc.raw_text, chunks=False)
	doc.unigrams = ngrams(tagged, n=1)
	classifier = OhanaBrendan([doc])
	jj_elements = classifier._extract_pos_tagged_element(doc, 'JJ')
	nns_elements = classifier._extract_pos_tagged_element(doc, 'NNS')
	assert len(jj_elements) == 1
	assert len(nns_elements) == 3
