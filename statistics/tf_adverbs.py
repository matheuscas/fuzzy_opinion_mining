import os
import pattern.en as pen
from pattern.en.wordnet import ADVERB
from pattern.search import search
from pattern.en import parsetree

file = open('adverbs.txt')
tf_adv = {}
advs = []
for w in file:
	tf_adv[w.split('\n')[0]] = 0
	advs.append(w.split('\n')[0])
file.close()

path_pos = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/pos'
path_neg = os.path.abspath(os.curdir) + '/corpora/cs_cornell_edu/txt_sentoken/neg'

files_pos = os.listdir(path_pos)
files_neg = os.listdir(path_neg)
documents = []

print "reading pos documents"
count = 1
for fn in files_pos:
	print count
	if fn.find('txt') != -1:
		fn_name = path_pos + '/' + fn
		text = open(fn_name).read()
		t = parsetree(text)
		text = text.split()
		for adv in advs:
			isBigram = True if len(search(adv + " JJ", t)) > 0 else False
			#isTrigram = True if len(search(adv + " RB JJ", t)) > 0 else False
			#isTrigram2 = True if len(search("RB " + adv + " JJ", t)) > 0 else False
			isNgram = isBigram #or isTrigram or isTrigram2
			if isNgram:
				qtd = text.count(adv)
				tf = tf_adv[adv]
				tf = tf + qtd
				tf_adv[adv] = tf
	count += 1

print "reading neg documents"
for fn in files_neg:
	print count
	if fn.find('txt') != -1:
		fn_name = path_neg + '/' + fn
		text = open(fn_name).read()
		t = parsetree(text)
		text = text.split()
		for adv in advs:
			isBigram = True if len(search(adv + " JJ", t)) > 0 else False
			#isTrigram = True if len(search(adv + " RB JJ", t)) > 0 else False
			#isTrigram2 = True if len(search("RB " + adv + " JJ", t)) > 0 else False
			isNgram = isBigram #or isTrigram or isTrigram2
			if isNgram:
				qtd = text.count(adv)
				tf = tf_adv[adv]
				tf = tf + qtd
				tf_adv[adv] = tf
	count += 1


sorted_tf_adv = sorted(tf_adv.items(), key=lambda x:x[1], reverse=True)
file = open('tf_adverbs.txt','w+')
for x in sorted_tf_adv:
	file.write(x[0] + ';' + str(x[1]) + "\n")
file.close()


