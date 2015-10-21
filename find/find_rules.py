import os, re
import xml.etree.ElementTree as ET
class Mention:
        def __init(self):
                self.begin = 0
                self.end = 0
                self.ID = 0
                self.fileName = ''

def find_rule(mention, parsefile):
	tree = ET.parse(parsefile)
	subtrees = tree.findall('.//node[@begin="' + str(mention.begin) + '"][@end="' + str(mention.end) + '"]')
	for subtree in subtrees:
		#TODO index
		attributes = subtree.attrib
		if 'word' in attributes:
			del attributes['begin']
			del attributes['end']
			del attributes['id']
			del attributes['sense']
			del attributes['word']
			del attributes['lemma']
			del attributes['root']
			# add volgende/vorig en parent node, dan naar regels zoeken!
		else:
			del attributes['begin']
			del attributes['end']
			del attributes['id']
			if 'cat' not in attributes:
				print attributes['rel']
			#if 'cat' in attributes and attributes['cat'] == 'np':
			#	print attributes['rel']
	if len(subtrees) == 0:
		pass #TODO
	#cat #rel
	#pos
	#vind parent node, of omringende pos?
def find_end(data, wordIdx, data_point):
        data_point = data_point[1:]
        if data_point[len(data_point)-1] == ')':
                return wordIdx + 1
        else:
                innerFound = False
                for i in range(wordIdx+1, len(data)):
                        for dataItr in data[i]:
                                if dataItr == '(' + data_point:
                                        innerFound = True
                                if data_point in dataItr and dataItr.endswith(')') and not dataItr.startswith('('):
                                        if innerFound:
                                                innerFound = False
                                        else:
                                                return i + 1
        print ("ERROR")

def find_mentions(data, parsefile, filename):
        for wordIdx in range(len(data)):
                for data_point in data[wordIdx]:
                        if data_point[0] == '(':
                                new_ment = Mention()
                                new_ment.begin = wordIdx

                                new_ment.end = find_end(data, wordIdx, data_point)
                                new_ment.ID = int(re.sub("\D", "", data_point))
                                new_ment.filename = filename
                                find_rule(new_ment, parsefile)


data_dir = '../clinDevData/'
for co_file in os.listdir(data_dir):
        if co_file.endswith('_ne') :
		pars_folder = data_dir + co_file[:co_file.find('_')] + '/'
                sents_data = []
		sent_data = []
                for line in open(data_dir + co_file):
			if line.startswith('#'):
				pass
                        elif len(line.split('\t')) > 2:
                                ref_id = line.split('\t')[len(line.split('\t'))-1][:-1]
                                sent_data.append(ref_id.split('|'))
			else:
				sents_data.append(sent_data)
				sent_data = []
		for i in range(len(sents_data)):
	                find_mentions(sents_data[i], pars_folder + str(i+1) + '.xml', co_file)


