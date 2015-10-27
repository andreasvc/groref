#!/usr/bin/env python

import colorama as c
import re, sys, os
import xml.etree.ElementTree as ET

### GLOBAL VARIABLES ###

# List of Dutch Stop words (http://www.ranks.nl/stopwords/dutch)
stopWords = ['aan', 'af', 'al', 'als', 'bij', 'dan', 'dat', 'die', 'dit', 'een', 'en', 'er', 'had', 'heb', 'hem', 'het', 'hij', 'hoe', 'hun', 'ik ', 'in', 'is', 'je', 'kan', 'me', 'men', 'met', 'mij', 'nog', 'nu', 'of', 'ons', 'ook', 'te', 'tot', 'uit', 'van', 'was ', 'wat', 'we', 'wel', 'wij', 'zal', 'ze', 'zei', 'zij', 'zo', 'zou']

# First available mentionID
mentionID = 0 

# List of implemented sieves
allSieves = [2, 5, 6, 7, 9]

### CLASSES ### 

# Class for 'mention'-objects
class Mention:
	'Class of mentions, containing features, IDs, links, etc.'
	def __init__(self, mentionID):
		self.ID = mentionID # ID can be used for mention ordering, but then ID assignment needs to be more intelligent/different
		self.sentNum = 0
		self.tokenList = []
		self.numTokens = 0
		self.begin = 0 # Token ID of first token
		self.end = 0 # Token ID of last token + 1
		self.type = '' # Pronoun, NP or Name
		self.clusterID = -1
		self.head_begin = 0 # Token ID of first head word, within tokenList
		self.head_end = 0
		self.headWords = []
		self.tokenAttribs = [] # List of dictionaries containing alpino output for each token/node
		
# Class for 'cluster'-objects
class Cluster:
	'Class of clusters, which contain features, an ID and a list of member-mentions-IDs'
	def __init__(self, clusterID):
		self.ID = clusterID
		self.mentionList = []

### READING AND WRITING ###

# Read in conll file, return list of lists containing a single word + annotation
def read_conll_file(fname):
	conll_list = []
	num_sentences = 0
	for line in open(fname, 'r'):
		split_line = line.strip().split('\t')
		if len(split_line) > 1:
			if split_line[0] != 'doc_id' and line[0] != '#': # Skip header and/or document tags
				conll_list.append(split_line)
		if not line.strip() or line == '#end document': # Empty line equals new sentence
			num_sentences += 1
	return conll_list, num_sentences
	
# Read in xml-files containing parses for sentences in document, return list of per-sentence XML trees
def read_xml_parse_files(fname):
	xml_tree_list = []
	dir_name = '/'.join(fname.split('/')[0:-1]) + '/' + fname.split('/')[-1].split('_')[0] + '/'
	xml_file_list = os.listdir(dir_name)
	delete_list = []
	for i in range (len(xml_file_list)):
		if not xml_file_list[i].endswith('.xml'):
			delete_list.append(i)
	for i in range (len(delete_list)):
		backwards = delete_list[(len(delete_list)-1)-i]
		del xml_file_list[backwards]
	# Sort list of filenames naturally (by number, not by alphabet)
	xml_file_list = [xml_file[:-4] for xml_file in xml_file_list]
	xml_file_list.sort(key=int)
	xml_file_list = [xml_file + '.xml' for xml_file in xml_file_list]
	for xml_file in xml_file_list:
		if re.search('[0-9].xml', xml_file):
			try:
				tree = ET.parse(dir_name + xml_file)
			except IOError:
				print 'Parse file not found: %s' % (xml_file)
		xml_tree_list.append(tree)
	return xml_tree_list
	
# Creates conll-formatted output with the clustering information
def generate_conll(docName, output_filename, doc_tags, sentenceDict, mention_dict):
	output_file = open(output_filename, 'w')
	docName = docName.split('/')[-1].split('_')[0]
	if doc_tags:
		output_file.write('#begin document (' + docName + '); part 000\n')
	for key in sorted(sentenceDict.keys()): # Cycle through sentences
		for token_idx, token in enumerate(sentenceDict[key].split(' ')): # Cycle through words in sentences
			corefLabel = ''
			for mention_id, mention in mention_dict.iteritems(): # Check all mentions, to see whether token is part of mention
				if mention.sentNum == key:
					if token_idx == mention.begin: # Start of mention, print a bracket
						if corefLabel:
							corefLabel += '|'
						corefLabel += '('
					if token_idx >= mention.begin and token_idx < mention.end:
						if corefLabel:
							if corefLabel[-1] != '(':
								corefLabel += '|'
						corefLabel += str(mention.clusterID)
					if token_idx + 1 == mention.end: # End of mention, print a bracket
						corefLabel += ')'
			if not corefLabel: # Tokens outside of mentions get a dash
				corefLabel = '-'
			output_file.write(docName + '\t' + str(key) + '\t' + '0\t' + '0\t' + '0\t' +
			'0\t' + token.encode('utf-8') + '\t' + corefLabel + '\n')
		output_file.write('\n')
	if doc_tags:
		output_file.write('#end document')	

### COREFERENCE SIEVE HELPERS ###

# Function that takes two mention ids, and merges the clusters they are part of, returns cluster dict and cluster_id_list
def mergeClustersByMentionIDs(idx1, idx2, mention_dict, cluster_dict, cluster_id_list):
	mention1 = mention_dict[idx1]
	mention2 = mention_dict[idx2]
	if mention1.clusterID == mention2.clusterID: # Cannot merge if mentions are part of same cluster
		return
	cluster1 = cluster_dict[mention1.clusterID]
	cluster2 = cluster_dict[mention2.clusterID]
	# Put all mentions of cluster2 in cluster1
	for mentionID in cluster2.mentionList:
		cluster_dict[mention1.clusterID].mentionList.append(mentionID)
		for mention_id, mention in mention_dict.iteritems():
			if mention.ID == mentionID:
				mention.clusterID = cluster1.ID
	del cluster_dict[cluster2.ID]
	cluster_id_list.remove(cluster2.ID)
	return cluster_dict, cluster_id_list
	
# Takes mention_id_list, returns a dict, with mention_ids per sentence
def get_mention_id_list_per_sentence(mention_id_list, mention_dict):
	mention_ids_per_sentence = {}
	for mention_id in mention_id_list:
		mention = mention_dict[mention_id]
		if mention.sentNum in mention_ids_per_sentence:
			mention_ids_per_sentence[mention.sentNum].append(mention.ID)
		else:
			mention_ids_per_sentence[mention.sentNum] = [mention.ID]
	return mention_ids_per_sentence
	
### MENTION DETECTION HELPERS ###
# Helper for mentionDetection()
def make_mention(begin, end, tree, mention_type, sentNum):
	global mentionID
	new_ment = Mention(mentionID)
	mentionID += 1
	new_ment.type = mention_type
	new_ment.begin = int(begin)
	new_ment.end = int(end)
	new_ment.numTokens = new_ment.end - new_ment.begin
	new_ment.sentNum = sentNum
	for node in tree.findall(".//node[@word]"):
		if int(node.attrib['begin']) >= int(begin) and int(node.attrib['end']) <= int(end):
			new_ment.tokenList.append(node.attrib["word"])
			new_ment.tokenAttribs.append(node.attrib)
	if mention_type.lower()[:2] == 'np':
		mention_node = tree.find(".//node[@cat='np'][@begin='" + begin + "'][@end='" + end + "']")
		head_node = mention_node.find("./node[@rel='hd']")
		new_ment.head_begin = int(head_node.attrib['begin']) - new_ment.begin
		new_ment.head_end = int(head_node.attrib['end']) - new_ment.begin
		new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
	elif mention_type.lower() == 'su': # Deal with su's in a hacky way
		mention_node = tree.find(".//node[@begin='" + begin + "'][@end='" + end + "']")
		if mention_node is not None:
			head_node = mention_node.find("./node[@rel='hd']")
			if head_node is not None:
				new_ment.head_begin = int(head_node.attrib['begin']) - new_ment.begin
				new_ment.head_end = int(head_node.attrib['end']) - new_ment.begin
				new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
			else:
				new_ment.head_begin = len(new_ment.tokenList) - 1
				new_ment.head_end = len(new_ment.tokenList)
				new_ment.headWords = new_ment.tokenList[-1:]
		else:
			new_ment.head_begin = len(new_ment.tokenList) - 1
			new_ment.head_end = len(new_ment.tokenList)
			new_ment.headWords = new_ment.tokenList[-1:]
	elif mention_type.lower() == 'name' or mention_type.lower()[:3] == 'mwu': # Add last part of names as headword
		new_ment.head_begin = len(new_ment.tokenList) - 1
		new_ment.head_end = len(new_ment.tokenList)
		new_ment.headWords = new_ment.tokenList[-1:]
	elif mention_type.lower() == 'noun':
		new_ment.head_begin = 0
		new_ment.head_end = 1
		new_ment.headWords = [new_ment.tokenList[0]]
	else: # Backup option
		if mention_type.lower() != 'pronoun':
			new_ment.head_begin = len(new_ment.tokenList) - 1
			new_ment.head_end = len(new_ment.tokenList)
			new_ment.headWords = new_ment.tokenList[-1:]
	return new_ment

# Stitch multi-word name mentions together
def stitch_names(node_list, tree, sentNum):
	node_list.sort(key=lambda node: int(node.attrib['begin']))
	added = [False] * len(node_list)
	mentions = []
	for beg_idx in range(len(node_list)):
		if not added[beg_idx]:
			added[beg_idx] = True
			beg_val = int(node_list[beg_idx].attrib['begin'])
			end_val = int(node_list[beg_idx].attrib['end'])
			for next_idx in range(beg_idx + 1, len(node_list)):
				if int(node_list[next_idx].attrib['begin']) == end_val:
					end_val += 1
					added[next_idx] = True
				else:
					break
			mentions.append(make_mention(beg_val, end_val, tree, 'name', sentNum))
	return mentions

# Sort mentions in list by sentNum, begin, end
def sort_mentions(mention_id_list, mention_dict):
	return sorted(mention_id_list, key = lambda x: (mention_dict[x].sentNum, mention_dict[x].begin, mention_dict[x].end))	

def add_mention(mention_list, new_mention):
	for old_mention in mention_list:
		if old_mention.begin == new_mention.begin and old_mention.end == new_mention.end and old_mention.sentNum == new_mention.sentNum:
			return mention_list
	mention_list.append(new_mention)
	return mention_list 
	
# Creates a cluster for each mention, fills in features
def initialize_clusters(mention_dict, mention_id_list):
	cluster_id_list = []
	cluster_dict = {}
	for mention_id in mention_id_list:
		mention = mention_dict[mention_id]
		new_cluster = Cluster(mention.ID) # Initialize with same ID as initial mention
		new_cluster.mentionList.append(mention.ID)
		mention_dict[mention_id].clusterID = new_cluster.ID
		cluster_dict[new_cluster.ID] = new_cluster
		cluster_id_list.append(new_cluster.ID)
	return cluster_dict, cluster_id_list, mention_dict
	
### MENTION PRINTING ###
	
# Human-readable printing of the output of the mention detection sieve	
def print_mentions_inline(sentenceDict, mention_id_list, mention_dict):
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention_id in mention_id_list:
				mention = mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print colour_text('[', 'red'),
					if mention.end == idx:
						print colour_text(']', 'red'),
					if idx + 1 == sentLength and mention.end == sentLength:
						closingBrackets += '] '
			print colour_text(token.encode('utf-8'), 'white'),
			print colour_text(closingBrackets, 'red'),
		print ''
		
# Human-readable printing of a comparison between the output of the mention detection sieve	and the 'gold' standard
# Green brackets are correct, gold/orange brackets are mention boundaries only found in the gold standard, and
# red brackets are only found in our output
def print_mention_analysis_inline(conll_list, sentenceDict, mention_id_list, mention_dict):
	doc_token_id = -1
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			gold_open = 0
			gold_close = 0
			resp_open = 0
			resp_close = 0
			doc_token_id += 1
			for mention_id in mention_id_list:
				mention = mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						resp_open += 1				
					if mention.end - 1 == idx:
						resp_close += 1
					elif idx + 1 == sentLength and mention.end == sentLength:
						resp_close += 1
			gold_open = len(re.findall('\(', conll_list[doc_token_id][-1]))
			gold_close = len(re.findall('\)', conll_list[doc_token_id][-1]))
			if gold_open >= resp_open:
				sys.stdout.write((gold_open - resp_open) * colour_text('[', 'yellow'))
				sys.stdout.write(resp_open * colour_text('[', 'green'))
			else:
				sys.stdout.write((resp_open - gold_open) * colour_text('[', 'red'))
				sys.stdout.write(gold_open * colour_text('[', 'green'))
				
			print colour_text(token.encode('utf-8'), 'white'),		
						
			if gold_close >= resp_close:
				sys.stdout.write((gold_close - resp_close) * colour_text(']', 'yellow'))
				sys.stdout.write(resp_close * colour_text(']', 'green') + ' ')
			else:
				sys.stdout.write((resp_close - gold_close) * colour_text(']', 'red'))
				sys.stdout.write(gold_close * colour_text(']', 'green') + ' ')								
		print ''
		
# Human-readable printing of gold standard mentions
def print_gold_mentions(conll_list, sentenceDict):
	doc_token_id = -1
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			gold_open = 0
			gold_close = 0
			doc_token_id += 1
			
			gold_open = len(re.findall('\(', conll_list[doc_token_id][-1]))
			gold_close = len(re.findall('\)', conll_list[doc_token_id][-1]))
			
			sys.stdout.write(gold_open * colour_text('[', 'yellow'))
			print colour_text(token.encode('utf-8'), 'white'),		
			sys.stdout.write(gold_close * colour_text(']', 'yellow') + ' ')								
		print ''	
		
# Human-readable printing of which mentions are clusterd by a given sieve
# Pre-sieve cluster IDs are in light blue, post-sieve cluster IDs (if changed) are in green
def print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict):
	linkings = {}
	for mention_id in mention_id_list:
		if mention_dict[mention_id].clusterID != old_mention_dict[mention_id].clusterID:
			linkings[old_mention_dict[mention_id].clusterID] = mention_dict[mention_id].clusterID
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention_id in mention_id_list:
				mention = old_mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print colour_text('[', 'red'),
						if mention.clusterID in linkings:
							print colour_text(str(mention.clusterID), 'cyan'),
							print colour_text(str(linkings[mention.clusterID]), 'green'),
						else:
							print colour_text(str(mention.clusterID), 'cyan'),						
					if mention.end == idx:
						print colour_text(']', 'red'),
					if idx + 1 == sentLength and mention.end == sentLength:
						closingBrackets += '] '			
			print colour_text(token.encode('utf-8'), 'white'),
			print colour_text(closingBrackets, 'red'),
		print ''
	
# Returns coloured text
def colour_text(text, colour):
	if colour.lower() == 'red':
		return c.Fore.RED + text + c.Fore.RESET
	elif colour.lower() == 'blue':
		return c.Fore.BLUE + text + c.Fore.RESET	
	elif colour.lower() == 'green':
		return c.Fore.GREEN + text + c.Fore.RESET	
	elif colour.lower() == 'white':
		return c.Fore.WHITE + text + c.Fore.RESET
	elif colour.lower() == 'yellow':
		return c.Fore.YELLOW + text + c.Fore.RESET		
	elif colour.lower() == 'cyan':
		return c.Fore.CYAN + text + c.Fore.RESET
		
# Prints all mentions and attributes in order		
def print_all_mentions_ordered(mention_id_list, mention_dict):
	for mention_id in mention_id_list:
		print mention_dict[mention_id].__dict__
		
### SCORING HELPERS ###

# Takes a scorer-output file, returns a dict with the scores
def process_conll_scorer_file(scorer_filename):
	scores = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'conll' : [], 'md' : []}
	metric = ''
	for metric in scores:
		scores[metric] = [0, 1, 0, 0, 1, 0, 0]
	with open(scorer_filename, 'r') as scores_file:
		for line in scores_file:
			if re.search('^METRIC', line):
				metric = re.split(' ', line)[-1][:-2] # Extract metric name
			if scores['md'] == [0, 1, 0, 0, 1, 0, 0]: # Avoid filling entry 5 times
				if re.search('^Identification', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores['md'] = values[0:6] + values[7:] # At index 6 is the '1' from 'F1', so ignore
			if metric == 'blanc':
				if re.search('^BLANC', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores[metric] = values[0:6] + values[7:]
			else:
				if re.search('^Coreference:', line):
					values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
					scores[metric] = values[0:6] + values[7:]
	scores['conll'] = [(scores['muc'][6] + scores['bcub'][6] + scores['ceafe'][6]) / 3] # Calculate CoNLL-F1
	return scores
