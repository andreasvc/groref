import os
import xml.etree.ElementTree as ET

data_dir = '../clinDevData/'
for co_file in os.listdir(data_dir):
	if co_file.endswith('_ne') :
		pars_folder = data_dir + co_file[:co_file.find('_')] + '/'
		for i in range(1,7):
			if os.path.exists(pars_folder + str(i) + '.xml'):
				tree = ET.parse(pars_folder + str(i) + '.xml')
				words = tree.findall('.//node[@cat="np"]')
				for node in words:
					print int(node.attrib['end']) - int(node.attrib['begin'])
					"""
					attributes = node.attrib
					del attributes['begin']
					del attributes['end']
					del attributes['id']
					del attributes['sense']
					del attributes['word']
					del attributes['lemma']
					del attributes['root']

					print attributes
					"""
					
