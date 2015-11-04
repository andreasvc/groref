import find_errors
import count_nodes

def clean_attrib(attrib, atr_dict):
    if attrib in atr_dict:
        del atr_dict[attrib]

def clean_attribs(attributes):
    for atr in ['begin', 'end', 'id', 'sense', 'word', 'lemma', 'root', 'mwu_sense', 'mwu_root']:
        clean_attrib(atr, attributes)
    return attributes

def create_dict(data):
	feats_dict = {}
	for word in data:
		for attrib in clean_attribs(word):
			featName = attrib + '_' + word[attrib]
			if word[attrib].find('(') > 0:
				featName = attrib + '_' + word[attrib][:word[attrib].find('(')]
			if featName in feats_dict:
				feats_dict[featName] += 1
			else:
				feats_dict[featName] = 1
	return feats_dict

if __name__ == '__main__':
	errors = find_errors.get_errors('../results/2015-11-04_14-17-11/')
	err_dict = create_dict(errors)
        for feature in sorted(err_dict, key=lambda l:err_dict[l]):
            print feature, err_dict[feature]
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
