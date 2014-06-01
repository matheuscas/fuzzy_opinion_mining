"""THIS WILL BE DEPRECATED"""

import pymongo
import os
from textblob import TextBlob, Word
from textblob.wordnet import ADV, ADJ, NOUN, VERB
from textblob_aptagger import PerceptronTagger
from bson.son import SON
from bson.code import Code
from pattern.search import search

POS_DOCS_PATH = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/pos'
NEG_DOCS_PATH = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/neg'
PENN_ADVERBS_TAGS = ['RB', 'RBR', 'RBS', 'RP']
PENN_ADJECTIVES_TAGS = ['JJ','JJR','JJS']
PENN_NOUNS_TAGS = ['NN','NNS','NNP','NNPS']
PENN_VERBS_TAGS = ['MD','VB','VBZ','VBP','VBD','VBN','VBG']
BIGRAM_PATTERNS = ["RB JJ","RB JJR", "RB JJS",
					"RBR JJ","RBR JJR", "RBR JJS",
					"RBS JJ","RBS JJR", "RBS JJS",
					"RP JJ","RP JJR", "RP JJS",
					"JJ NN", "JJ NNS","JJ JJ","NN JJ","NNS JJ"] # Turney's bigrams between JJ and NN




REDUCER = Code("""
                function (key, values) {
                  var total = 0;
                  for (var i = 0; i < values.length; i++) {
                    total += values[i];
                  }
                  return total;
                }
                """)


def get_mongo_client(domain='localhost', port=27017):
    return pymongo.MongoClient(domain, port)

def create_cornell_mongo_db():

	files_pos = os.listdir(POS_DOCS_PATH)
	files_neg = os.listdir(NEG_DOCS_PATH)

	client = get_mongo_client()
	cornell = client['cornell']
	documents = cornell['documents']

	for fn in files_pos:
		if fn.find('txt') != -1:
			fn_name = POS_DOCS_PATH + '/' + fn
			doc = {'name': fn,
					'text':open(fn_name).read(),
					'polarity':1}
			documents.insert(doc)

	for fn in files_neg:
		if fn.find('txt') != -1:
			fn_name = NEG_DOCS_PATH + '/' + fn
			doc = {'name': fn,
					'text':open(fn_name).read(),
					'polarity':0}

			documents.insert(doc)

	return cornell

def extract_all_documents_adverbs(client):

	cornell = client['cornell']
	documents = cornell['documents']
	for doc in documents.find():
		blob = TextBlob(doc['text'])
		advs = []
		for word, tag in blob.tags:
			is_adv = len(Word(word).get_synsets(pos=ADV)) > 0
			if tag in PENN_ADVERBS_TAGS and is_adv:
				advs.append(word)
		documents.update({'name':doc['name']},{'$set':{'adverbs':advs}})

def extract_all_documents_nouns(client):
	documents = client['cornell']['documents']
	for doc in documents.find():
		blob = TextBlob(doc['text'])
		nouns = []
		for word, tag in blob.tags:
			is_noun = len(Word(word).get_synsets(pos=NOUN)) > 0
			if tag in PENN_NOUNS_TAGS and is_noun:
				nouns.append(word)
		documents.update({'name':doc['name']},{'$set':{'nouns':nouns}})

def extract_all_documents_adjectives(client):

	cornell = client['cornell']
	documents = cornell['documents']

	for doc in documents.find():
		blob = TextBlob(doc['text'])
		adjs = []
		for word, tag in blob.tags:
			is_adj = len(Word(word).get_synsets(pos=ADJ)) > 0
			if tag in PENN_ADJECTIVES_TAGS and is_adj:
				adjs.append(word)
		documents.update({'name':doc['name']},{'$set':{'adjectives':adjs}})

def extract_all_documents_verbs(client):
	documents = client['cornell']['documents']
	for doc in documents.find():
		blob = TextBlob(doc['text'])
		verbs = []
		for word,tag in blob.tags:
			is_verb = len(Word(word).get_synsets(pos=VERB)) > 0
			if tag in PENN_VERBS_TAGS and is_verb:
				verbs.append(word)
		documents.update({'name':doc['name']},{'$set':{'verbs':verbs}})

def extract_ngrams_documents_elements(client):

	cornell = client['cornell']
	documents = cornell['documents']
	for doc in documents.find():
		ngrams_adverbs = []
		ngrams_adjectives = []
		for bigram in doc['bigrams']:
			element_1 = bigram[0].split('/')
			element_2 = bigram[1].split('/')
			if element_1[1] in PENN_ADVERBS_TAGS:
				ngrams_adverbs.append(element_1[0])

			if element_2[1] in PENN_ADJECTIVES_TAGS:
				ngrams_adjectives.append(element_2[0])
		documents.update({'name':doc['name']},{'$set':{'ngrams_adverbs':ngrams_adverbs}})
		documents.update({'name':doc['name']},{'$set':{'ngrams_adjectives':ngrams_adjectives}})

def adverbs_map_reduce(client):
	mapper = Code("""
               function () {
                 this.adverbs.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

	results = client['cornell']['documents'].map_reduce(mapper, REDUCER, 'tempresults')
	sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
	client['cornell']['tempresults'].drop()
	adverbs_tf = client['cornell']['adverbs_tf']
	adverbs_tf.insert(sorted_results)
	return sorted_results

def ngrams_adverbs_map_reduce(client):
	mapper = Code("""
               function () {
                 this.ngrams_adverbs.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

	results = client['cornell']['documents'].map_reduce(mapper, REDUCER, 'tempresults')
	sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
	client['cornell']['tempresults'].drop()
	ngrams_adverbs_tf = client['cornell']['ngrams_adverbs_tf']
	ngrams_adverbs_tf.insert(sorted_results)
	return sorted_results

def adjectives_map_reduce(client):
	mapper = Code("""
               function () {
                 this.adjectives.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

	results = client['cornell']['documents'].map_reduce(mapper, REDUCER, 'tempresults')
	sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
	client['cornell']['tempresults'].drop()
	adjectives_tf = client['cornell']['adjectives_tf']
	adjectives_tf.insert(sorted_results)
	return sorted_results

def ngrams_adjectives_map_reduce(client):
	mapper = Code("""
               function () {
                 this.ngrams_adjectives.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

	results = client['cornell']['documents'].map_reduce(mapper, REDUCER, 'tempresults')
	sorted_results = sorted(results.find(), key=lambda k: k['value'], reverse=True)
	client['cornell']['tempresults'].drop()
	ngrams_adjectives_tf = client['cornell']['ngrams_adjectives_tf']
	ngrams_adjectives_tf.insert(sorted_results)
	return sorted_results

def get_valid_bigrams(wordlists):
	valids = []
	for wordlist in wordlists:
		word1 = wordlist[0]
		word2 = wordlist[1]
		tags1 = word1.split('/')
		tags2 = word2.split('/')
		if len(tags1) > 1 and len(tags2) > 1:
			pattern = tags1[1] + " " + tags2[1]
			if pattern in BIGRAM_PATTERNS:
				valids.append((word1.split('/')[0] + "/" + tags1[1],
								word2.split('/')[0] + "/" + tags2[1]))
	return valids

def get_valid_trigrams(wordlists):
	valids = []
	for wordlist in wordlists:
		first_w = wordlist[0]
		second_w = wordlist[1]
		third_w = wordlist[2]
		tags1 = first_w.split('/')
		tags2 = second_w.split('/')
		tags3 = third_w.split('/')
		if len(tags1) > 1 and len(tags2) > 1 and len(tags3) > 1:
			if tags1[1] in PENN_ADVERBS_TAGS and tags2[1] in PENN_ADVERBS_TAGS and tags3 in PENN_ADJECTIVES_TAGS:
				valids.append((first_w.split('/')[0] + "/" + tags1[1],
								second_w.split('/')[0] + "/" + tags2[1],
								third_w.split('/')[0] + "/" + tags3[1]))
	return valids

def extract_bigrams(client):
	documents = client['cornell']['documents']

	for doc in documents.find():
		blob = TextBlob(doc['text'])
		valid_bigrams = []
		for s in blob.sentences:
			sentence = TextBlob(s.dict['raw'])
			sentence = TextBlob(sentence.parse())
			bigrams = sentence.ngrams(n=2)
			valid_bigrams = valid_bigrams + get_valid_bigrams(bigrams)
		documents.update({'name':doc['name']},{'$set':{'bigrams':valid_bigrams}})

def extract_trigrams(client):
	documents = client['cornell']['documents']

	for doc in documents.find():
		blob = TextBlob(doc['text'])
		valid_trigrams = []
		for s in blob.sentences:
			sentence = TextBlob(s.dict['raw'])
			sentence = TextBlob(sentence.parse())
			trigrams = sentence.ngrams(n=3)
			valid_trigrams = valid_trigrams + get_valid_trigrams(trigrams)
		documents.update({'name':doc['name']},{'$set':{'trigrams':valid_trigrams}})

def get_unique_adverbs(client):

	cornell = client['cornell']
	documents = cornell['documents']
	advs = []
	for doc in documents.find():
		advs = advs + doc['adverbs']

	return set(advs)

def get_unique_adjectives(client):

	cornell = client['cornell']
	documents = cornell['documents']
	adjs = []
	for doc in documents.find():
		adjs = adjs + doc['adjectives']

	return set(adjs)

def create_collection_from_file(mongo_client, file_name, collection_name):
	"""File must have only one word per line"""

	f = open(file_name)
	collection = mongo_client['cornell'][collection_name]
	for line in f.readlines():
		collection.insert({'word':line.split('\n')[0]}) #just the word. no carriage return
	f.close()

def create_or_update_collection_from_file(mongo_client, file_name, collection_name):
	""" File must have only a pair of values per line, separated by ; """

	f = open(file_name)
	collection = mongo_client['cornell'][collection_name]
	for line in f.readlines():
		values = line.split('\n')[0]
		values = values.split(';')
		adverb = values[0]
		factor = values[1]
		collection.insert({'word':adverb,'factor':factor})
	f.close()

def tag_documents_text(client):

	documents = client['cornell']['documents']
	for doc in documents.find():
		blob = TextBlob(doc['text'], pos_tagger=PerceptronTagger())
		parsed_blob = blob.parse()
		documents.update({'name':doc['name']},{'$set':{'parsed_perceptron':parsed_blob}})
