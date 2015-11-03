import find_errors
import count_nodes

def create_dict(data):
	feats_dict = {}
	for word in data:
		for attrib in word:
			featName = attrib + '_' + word[attrib]
			if word[attrib].find('(') > 0:
				featName = attrib + '_' + word[attrib][:word[attrib].find('(')]
			if featName in feats_dict:
				feats_dict[featName] += 1
			else:
				feats_dict[featName] = 1
	return feats_dict

"""
def clean_attribs(atr_dict):
    del attributes['begin']
    del attributes['end']
    del attributes['id']
    del attributes['sense']
    del attributes['word']
    del attributes['lemma']
    del attributes['root']
"""
if __name__ == '__main__':
	errors = find_errors.get_errors()
	err_dict = create_dict(errors)
	"""
	all_counts = count_nodes.get_total_counts()
	all_dict = create_dict(all_counts)

	results = []
	for featName in err_dict:
		if featName in all_dict:
			results.append([float(err_dict[featName])/all_dict[featName], featName, err_dict[featName], all_dict[featName]])

	for feature in sorted(results, key=lambda l:l[0]):
		print feature
	print(len(errors))
	print(len(all_counts))
	"""
