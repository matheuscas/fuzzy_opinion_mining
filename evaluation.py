import domain
import decimal

def precision(qtd_true_positives, list_of_true_negative_documents):
	"""TP / (TP + FP)
	TP - True Positive
	FP - False Positive - a document is negative but classified as positive
	"""

	fp = 0
	for d in list_of_true_negative_documents:
		if d.predicted_polarity > 0:
			fp = fp + 1
	qtd_true_positives = decimal.Decimal(qtd_true_positives)
	fp = decimal.Decimal(fp)
	return (qtd_true_positives / (qtd_true_positives + fp))

def recall(qtd_true_positives, list_of_true_positive_documents):
	"""
	TP / (TP + FN)
	TP - True Positive
	FN - False Negative - a document is positive but was classified as negative
	"""

	fn = 0
	for d in list_of_true_positive_documents:
		if d.predicted_polarity < 0:
			fn = fn + 1
	qtd_true_positives = decimal.Decimal(qtd_true_positives)
	fn = decimal.Decimal(fn)
	return (qtd_true_positives / (qtd_true_positives + fn))

def accuracy(qtd_true_positives, qtd_true_negatives, all_documents):
	"""
	(TP + TN) / (TP + TN + FP + FN)
	TP - True positives
	TN - True negatives
	FP - False Positive - a document is negative but classified as positive
	FN - False Negative - a document is positive but was classified as negative
	"""

	fp = fn = 0
	for d in all_documents:
		if d.polarity == domain.Document.POSITIVE and d.predicted_polarity < 0:
			fn = fn + 1
		elif d.polarity == domain.Document.NEGATIVE	and d.predicted_polarity > 0:
			fp = fp + 1

	fp = decimal.Decimal(fp)
	fn = decimal.Decimal(fn)
	qtp = decimal.Decimal(qtd_true_positives)
	qtn = decimal.Decimal(qtd_true_negatives)

	return (qtp + qtn) /(qtp + qtn + fp + fn)


