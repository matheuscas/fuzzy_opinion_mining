import model
from bson.code import Code
import transformation
import xlsxwriter

def search_in_list_of_dicts(list_of_dicts,key,val):
	try:
		return (item for item in list_of_dicts if item[key] == val).next()
	except Exception, e:
		return {}

mongo_client = model.get_mongo_client()
adjectives = mongo_client.cornell.adjectives_tf
adverbs = mongo_client.cornell.adverbs_tf

documents = mongo_client.cornell.documents
positives = mongo_client.cornell.positives
negatives = mongo_client.cornell.negatives
non_grading = mongo_client.cornell.non_grading_adv
intensifiers = mongo_client.cornell.intensifiers_adv
attenuators = mongo_client.cornell.attenuators_adv

qtd_comments = 1000.0

adverbs_mapper = Code("""
               function () {
                 this.adverbs.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

adjectives_mapper = Code("""
               function () {
                 this.adjectives.forEach(function(z) {
                   emit(z, 1);
                 });
               }
               """)

#ADVERBS
results = mongo_client['cornell']['positives'].map_reduce(adverbs_mapper, model.REDUCER, 'tempresults')
positive_adverbs_occurences = sorted(results.find(), key=lambda k: k['value'], reverse=True)
mongo_client['cornell']['tempresults'].drop()

results = mongo_client['cornell']['negatives'].map_reduce(adverbs_mapper, model.REDUCER, 'tempresults')
negative_adverbs_occurences = sorted(results.find(), key=lambda k: k['value'], reverse=True)
mongo_client['cornell']['tempresults'].drop()

#ADJECTIVES
results = mongo_client['cornell']['positives'].map_reduce(adjectives_mapper, model.REDUCER, 'tempresults')
positive_adjective_occurences = sorted(results.find(), key=lambda k: k['value'], reverse=True)
mongo_client['cornell']['tempresults'].drop()

results = mongo_client['cornell']['negatives'].map_reduce(adjectives_mapper, model.REDUCER, 'tempresults')
negative_adjective_occurences = sorted(results.find(), key=lambda k: k['value'], reverse=True)
mongo_client['cornell']['tempresults'].drop()

adv_words_probs = []
print "adverbs..."
for adv in adverbs.find():
	pos_elem = search_in_list_of_dicts(positive_adverbs_occurences, "_id", adv["_id"])
	neg_elem = search_in_list_of_dicts(negative_adverbs_occurences, "_id", adv["_id"])

	name = ""
	pos_prob = 0.0
	neg_prob = 0.0
	set_name = "none"

	if len(pos_elem) > 0:
		name = pos_elem["_id"]
		#print 'DID find ' + adv["_id"] + ' in positives'
		pos_prob = (pos_elem["value"] / qtd_comments)
	elif len(pos_elem) == 0:
		#print 'did not find ' + adv["_id"] + ' in positives'
		name = adv["_id"]
		count = 0.0
		for pos in positives.find():
			count = count + pos['text'].count(adv["_id"])
		pos_prob = (count / qtd_comments)

	if len(neg_elem) > 0:
		#print 'DID find ' + adv["_id"] + ' in negatives'
		name = neg_elem["_id"]
		neg_prob = (neg_elem["value"] / qtd_comments)
	elif len(neg_elem) == 0:
		#print 'did not find ' + adv["_id"] + ' in negatives'
		name = adv["_id"]
		count = 0.0
		for neg in negatives.find():
			count = count + neg['text'].count(adv['_id'])
		neg_prob = (count / qtd_comments)

	if len(search_in_list_of_dicts(non_grading.find(),'word',adv["_id"])) > 0:
		set_name = 'non_grading_adv'
	elif len(search_in_list_of_dicts(intensifiers.find(),'word',adv["_id"])) > 0:
		set_name = 'intensifier'
	elif len(search_in_list_of_dicts(attenuators.find(),'word',adv["_id"])):
		set_name = 'attenuator'

	swn = transformation.word_polarity(name,pos_tag="ADVERB")
	if swn:
		swn = swn[0]
	adv_words_probs.append((name, pos_prob, neg_prob, set_name, swn, pos_prob - neg_prob))

# workbook = xlsxwriter.Workbook('adverbs_probabilities.xlsx')
# worksheet = workbook.add_worksheet()
# worksheet.set_column('A:B', 20)
# worksheet.set_column('A:C', 20)
# worksheet.set_column('A:D', 20)
# worksheet.write('A1','ADVERB')
# worksheet.write('B1','P(ADVERB|POSITIVES)')
# worksheet.write('C1','P(ADVERB|NEGATIVES)')
# worksheet.write('D1','SET')
# line = 1
# for adv_prob in adv_words_probs:
# 	worksheet.write(line, 0, adv_prob[0])
# 	worksheet.write(line, 1, adv_prob[1])
# 	worksheet.write(line, 2, adv_prob[2])
# 	worksheet.write(line, 3, adv_prob[3])
# 	line = line + 1

# workbook.close()

mongo_client = model.get_mongo_client()
for adv_prob in adv_words_probs:
	mongo_client.cornell.p_adv.insert({"word":adv_prob[0],"p_pos":adv_prob[1],
										"p_neg":adv_prob[2],"set":adv_prob[3],
										"swn":adv_prob[4],"p_polarity":adv_prob[5]})

print "adverbs...DONE"

print "adjectives..."

adj_words_probs = []
for adj in adjectives.find():
	pos_elem = search_in_list_of_dicts(positive_adjective_occurences, "_id", adj["_id"])
	neg_elem = search_in_list_of_dicts(negative_adjective_occurences, "_id", adj["_id"])

	name = ""
	pos_prob = 0.0
	neg_prob = 0.0
	set_name = "none"

	if len(pos_elem) > 0:
		name = pos_elem["_id"]
		#print 'DID find ' + adj["_id"] + ' in positives'
		pos_prob = (pos_elem["value"] / qtd_comments)
	elif len(pos_elem) == 0:
		#print 'did not find ' + adj["_id"] + ' in positives'
		name = adj["_id"]
		count = 0.0
		for pos in positives.find():
			count = count + pos['text'].count(adj["_id"])
		pos_prob = (count / qtd_comments)

	if len(neg_elem) > 0:
		#print 'DID find ' + adj["_id"] + ' in negatives'
		name = neg_elem["_id"]
		neg_prob = (neg_elem["value"] / qtd_comments)
	elif len(neg_elem) == 0:
		#print 'did not find ' + adj["_id"] + ' in negatives'
		name = adj["_id"]
		count = 0.0
		for neg in negatives.find():
			count = count + neg['text'].count(adj['_id'])
		neg_prob = (count / qtd_comments)

	swn = transformation.word_polarity(name)
	if swn:
		swn = swn[0]
	adj_words_probs.append((name, pos_prob, neg_prob, swn, pos_prob - neg_prob))

# workbook = xlsxwriter.Workbook('adjectives_probabilities.xlsx')
# worksheet = workbook.add_worksheet()
# worksheet.set_column('A:B', 20)
# worksheet.set_column('A:C', 20)
# worksheet.set_column('A:D', 30)
# worksheet.write('A1','ADJECTIVE')
# worksheet.write('B1','P(ADJECTIVE|POSITIVES)')
# worksheet.write('C1','P(ADJECTIVE|NEGATIVES)')
# worksheet.write('D1','SENTIWORDNET POLARITY')
# line = 1
# for adj_prob in adj_words_probs:
# 	worksheet.write(line, 0, adj_prob[0])
# 	worksheet.write(line, 1, adj_prob[1])
# 	worksheet.write(line, 2, adj_prob[2])
# 	worksheet.write(line, 3, adj_prob[3])
# 	line = line + 1

# workbook.close()

for adj_prob in adj_words_probs:
	mongo_client.cornell.p_adj.insert({"word":adj_prob[0],"p_pos":adj_prob[1],
										"p_neg":adj_prob[2],"swn":adj_prob[3],
										"p_polarity":adj_prob[4]})

print "adjectives...DONE"


