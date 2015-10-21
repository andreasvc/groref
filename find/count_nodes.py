import os
import xml.etree.ElementTree as ET

data_dir = '../clinDevData/'
for co_file in os.listdir(data_dir):
	if co_file.endswith('_ne') :
		pars_folder = data_dir + co_file[:co_file.find('_')] + '/'
		for i in range(1,7):
			if os.path.exists(pars_folder + str(i) + '.xml'):
				tree = ET.parse(pars_folder + str(i) + '.xml')
				words = tree.findall('.//node')
				for node in words:
					if 'cat' not in node.attrib:
						print node.attrib['rel']
			
