import os, re, pickle
import xml.etree.ElementTree as ET

class Mention:
        def __init(self):
                self.begin = 0
                self.end = 0
                self.ID = 0
                self.filename = ''
		self.parsefile = ''
atr = []
def find_attributes(mention, types):
	global atr
	tree = ET.parse(mention.parsefile)
	subtrees = tree.findall('.//node[@begin="' + str(mention.begin) + '"][@end="' + str(mention.end) + '"]')
	for subtree in subtrees:
		attributes = subtree.attrib
		if 'word' in attributes and 1 in types:
			atr.append(attributes)
                elif 2 in types:
			atr.append(attributes)

	if len(subtrees) == 0 and 3 in types:
		atr.append([])

def found(mention, mentionList):
	for mentionItr in mentionList:
		if mention.parsefile == mentionItr.parsefile and mention.begin == mentionItr.begin and mention.end == mentionItr.end:
			return True
	return False

def find_errors(mentions_gold, mentions_own, types):
	for mention in mentions_gold: #TODO, other way around for precision
		if not found(mention, mentions_own):
			  find_attributes(mention, types)


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

def find_mentions(filename, co_file):
	sents_data = []
	sent_data = []
	for line in open(filename):
		if line.startswith('#'):
			pass
		elif len(line.split('\t')) > 2:
			ref_id = line.split('\t')[len(line.split('\t'))-1][:-1]
			sent_data.append(ref_id.split('|'))
		else:
			sents_data.append(sent_data)
			sent_data = []
	mentions = []
	for i in range(len(sents_data)):
		data = sents_data[i]
	        for wordIdx in range(len(data)):
			if len(set(data[wordIdx])) != len(data[wordIdx]):
				#print 'Double'
				pass #TODO fix
			else:
		                for data_point in data[wordIdx]:
        		                if data_point[0] == '(':
                		                new_ment = Mention()
                        		        new_ment.begin = wordIdx

                	                	new_ment.end = find_end(data, wordIdx, data_point)
		                                new_ment.ID = int(re.sub("\D", "", data_point))
	        	                        new_ment.filename = co_file
						new_ment.parsefile = '../clinDevData/'+co_file[:co_file.find('_')] + '/' + str(i+1) + '.xml'
                	                	mentions.append(new_ment)
	return mentions

def get_errors(types):
    gold_dir = '../clinDevData/'
    own_dir = '../results/res/'
    for co_file in os.listdir(gold_dir):
        if co_file.endswith('_ne') :
		mentions_gold = find_mentions(gold_dir + co_file, co_file)
		mentions_own = find_mentions(own_dir + co_file + '.coref', co_file)
		find_errors(mentions_gold, mentions_own, types)

    return(atr)
