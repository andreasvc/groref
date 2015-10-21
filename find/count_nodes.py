import os, pickle
import xml.etree.ElementTree as ET

attr_words = []
data_dir = '../clinDevData/'
for co_file in os.listdir(data_dir):
	if co_file.endswith('_ne') :
		pars_folder = data_dir + co_file[:co_file.find('_')] + '/'
		for i in range(1,7):
			if os.path.exists(pars_folder + str(i) + '.xml'):
				tree = ET.parse(pars_folder + str(i) + '.xml')
				words = tree.findall('.//node[@word]')
				for node in words:
					attributes = node.attrib
					del attributes['begin']
					del attributes['end']
					del attributes['id']
					del attributes['sense']
					del attributes['word']
					del attributes['lemma']
					del attributes['root']
					if 'ntype' in attributes and attributes['ntype'] == 'soort' and 'rel' in attributes and attributes['rel'] == 'obj1':
						attr_words.append(attributes)
print(len(attr_words))
pickle.dump(attr_words, open('all.pickle', 'wb'))
			
