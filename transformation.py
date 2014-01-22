from pattern.en import wordnet
from pattern.en import NOUN, VERB, ADJECTIVE, ADVERB

def word_polarity(word, pos_tag=None):
	"""returns a (polarity, subjectivity)-tuple for the given word
	The word can be NOUN, VERB, ADJECTIVE, ADVERB"""

	TAGS = {"NOUN":NOUN, "VERB":VERB, "ADJECTIVE":ADJECTIVE, "ADVERB":ADVERB}
	TAG = TAGS[pos_tag] if pos_tag else ADJECTIVE

	return wordnet.synsets(word, TAG)