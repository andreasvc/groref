#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Entity coreference resolution system for the CLIN26 Shared Task.
Based on the Stanford Coreference Resolution system. Requires CoNLL-formatted
input data and Alpino pars in xml as input, gives CoNLL-formatted output. """

import argparse, re, copy
from utils import *
from sieveDummy import sieveDummy
from sieveHeadMatch import sieveHeadMatch

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

# Stitch multi-word name mentions together
def stitch_names(mention_id_list, mention_dict):
	stitched_mention_id_list = []
	stitched_mention_dict = {}
	idx = 0
	# Assume all split names are sequential in mention_id_list
	while idx < len(mention_id_list):
		mention_id = mention_id_list[idx] 
		if mention_dict[mention_id].type == "Name": # Ignore non-names
			inc = 1 # How far to search ahead
			continueSearch = True
			while continueSearch:
				if idx + inc < len(mention_id_list):
					lookup_mention_id = mention_id_list[idx + inc]
					# Mentions should be part of same sentence
					if mention_dict[lookup_mention_id].begin == mention_dict[mention_id].end and mention_dict[lookup_mention_id].sentNum == mention_dict[mention_id].sentNum:
						mention_dict[mention_id].end = mention_dict[lookup_mention_id].end
						mention_dict[mention_id].numTokens += mention_dict[lookup_mention_id].numTokens
						mention_dict[mention_id].tokenList += mention_dict[lookup_mention_id].tokenList
						inc += 1 # Stitched one part to the current mention, now check the mention after that
					else:
						continueSearch = False
				else:
					continueSearch = False
			stitched_mention_id_list.append(mention_id)
			idx += inc # If 3 parts stitched together, skip the subsequent 2 mentions
		else:
			stitched_mention_id_list.append(mention_id)
			idx += 1
	# Remove mentions that have been stitched together
	stitched_mention_dict = {idx : mention_dict[idx] for idx in stitched_mention_id_list} 
	return stitched_mention_id_list, stitched_mention_dict

# remove duplicate mentions
def remove_duplicates(mention_id_list, mention_dict):
	remove_ids = []
	for i in range(len(mention_id_list)): #sentnum, begin and end
		this_sentNum = mention_dict[mention_id_list[i]].sentNum
		this_begin = mention_dict[mention_id_list[i]].begin
		this_end = mention_dict[mention_id_list[i]].end
		for j in range(i+1, len(mention_id_list)):
			if (this_sentNum == mention_dict[mention_id_list[j]].sentNum and 
				this_begin == mention_dict[mention_id_list[j]].begin and 
				this_end == mention_dict[mention_id_list[j]].end):
				remove_ids.append(mention_id_list[i])
				break
	for remove_id in remove_ids:
		mention_id_list.remove(remove_id)
		del mention_dict[remove_id]
	return mention_id_list, mention_dict

# Sort mentions in list by sentNum, begin, end
def sort_mentions(mention_id_list, mention_dict):
	return sorted(mention_id_list, key = lambda x: (mention_dict[x].sentNum, mention_dict[x].begin, mention_dict[x].end))

# Helper for detect_mentions()
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
	if mention_type == 'Name': # Add last part of names as headword
		new_ment.head_begin = len(new_ment.tokenList) - 1
		new_ment.head_end = len(new_ment.tokenList)
		new_ment.headWords = new_ment.tokenList[-1:]
	if mention_type == 'noun':
		new_ment.head_begin = 0
		new_ment.head_end = 1
		new_ment.headWords = [new_ment.tokenList[0]]
	return new_ment

# Mention detection sieve, selects all NPs, pronouns, names		
def detect_mentions(conll_list, tree_list, docFilename, verbosity, sentenceDict):
#	global mentionID, sentenceDict
	mention_id_list = []
	mention_dict = {}
	for tree in tree_list:
		mention_list = []
		
		sentNum = tree.find('comments').find('comment').text
		sentNum = int(re.findall('#[0-9]+', sentNum)[0][1:])
		sentenceDict[int(sentNum)] = tree.find('sentence').text
		
		np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
		for mention_node in tree.findall(".//node[@cat='np']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in np_rels and len_ment < 7: 
				name = 'np_' + mention_node.attrib['rel']
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum))
		
		mwu_rels = ['obj1','su','cnj'] #hd 14/65 
		for mention_node in tree.findall(".//node[@cat='mwu']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
				name = 'mwu_' + mention_node.attrib['rel']
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum))

		for mention_node in tree.findall(".//node"):
			if 'cat' not in mention_node.attrib and mention_node.attrib['rel'] == 'su':
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'su', sentNum))
		
		for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'noun', sentNum))
	
		for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Pronoun', sentNum))

		# Take all name elements, some of which might be parts of same name. Those are stitched together later.
		for mention_node in tree.findall(".//node[@pos='name']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Name', sentNum))


		#TODO, look at children nodes, vooral bij relaties met lage precisie!
		
		"""	
		for mention_node in tree.findall(".//node[@cat='np']"):
			new_ment = make_mention(mention_node, 'NP', sentNum)
			new_ment.tokenList = []
			for node in mention_node.iter():
				if "word" in node.attrib:
					if 'pos' in node.attrib and node.attrib['pos'] == 'adv' and int(new_ment.begin) == int(node.attrib['begin']):
						#if np starts with adv, remove
						new_ment.begin = new_ment.begin + 1
						new_ment.numTokens = new_ment.numTokens - 1
					else: 
						new_ment.tokenList.append(node.attrib["word"])
			mention_list.append(new_ment)
		"""

		if len(tree.findall('.//node')) > 2: 
			for mention in mention_list:
				mention_id_list.append(mention.ID)
				mention_dict[mention.ID] = mention
		if verbosity == 'high':
			print 'Detecting mentions in sentence number %s' % (sentNum)
			print 'NP:   %d' % (len(tree.findall(".//node[@cat='np']")))
			print 'NP2:  %d' % (len(tree.findall(".//node[@lcat='np'][@ntype='soort']")))
			print 'DetN: %d' % (len(tree.findall(".//node[@pos='det']../node[@pos='noun']")))
			print 'MWU:  %d' % (len(tree.findall(".//node[@cat='mwu']")))
			print 'DU:   %d' % (len(tree.findall(".//node[@cat='du']")))
			print 'PRON: %d' % (len(tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']")))
	# Stitch together split name-type mentions
	mention_id_list, mention_dict = stitch_names(mention_id_list, mention_dict)
	#remove duplicates:
	bef_dup = len(mention_id_list)	
	mention_id_list, mention_dict = remove_duplicates(mention_id_list, mention_dict)
	# Sort list properly
	mention_id_list = sort_mentions(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'found %d unique mentions' % (len(mention_id_list))
		print 'and %d duplicates (which are removed)' % (bef_dup - len(mention_id_list))
	return mention_id_list, mention_dict	
		
# Creates a cluster for each mention, fills in features
def initialize_clusters(mention_dict):
	cluster_id_list = []
	cluster_dict = {}
	for mention_id, mention in mention_dict.iteritems():
		new_cluster = Cluster(mention.ID) # Initialize with same ID as initial mention
		new_cluster.mentionList.append(mention.ID)
		mention.clusterID = new_cluster.ID
		cluster_dict[new_cluster.ID] = new_cluster
		cluster_id_list.append(new_cluster.ID)
	return cluster_dict, cluster_id_list, mention_dict

def main(input_file, output_file, doc_tags, verbosity):
	num_sentences = 9999 # Maximum number of sentences for which to read in parses
	# Read input files
	try:
		conll_list, num_sentences = read_conll_file(input_file)
	except IOError:
		print 'CoNLL input file not found: %s' % (input_file)
	xml_tree_list = read_xml_parse_files(input_file)[:num_sentences]
	if verbosity == 'high':
		print 'Number of sentences found: %d' % (num_sentences)
		print 'Number of xml parse trees used: %d' % (len(xml_tree_list))
	sentenceDict = {} # Initialize dictionary containing sentence strings
	# Do mention detection, give back 3 global variables:
	## mention_id_list contains list of mention IDs in right order, for traversing in sieves
	## mention_dict contains the actual mentions, format: {id: Mention}
	## cluster_dict contains all clusters, in a dict
	mention_id_list, mention_dict = detect_mentions(conll_list, xml_tree_list, input_file, verbosity, sentenceDict)
	if verbosity == 'high':
		print 'OUR MENTION OUTPUT:'
		print_mentions_inline(sentenceDict, mention_id_list, mention_dict)
		print 'MENTION DETECTION OUTPUT VS. GOLD STANDARD:'
		print_mention_analysis_inline(conll_list, sentenceDict, mention_id_list, mention_dict)								
	cluster_dict, cluster_id_list, mention_dict = initialize_clusters(mention_dict)
	## APPLY SIEVES HERE
	## strictest head matching sieve	
	old_mention_dict = copy.deepcopy(mention_dict) # Store to print changes afterwards
	mention_id_list, mention_dict, cluster_dict, cluster_id_list = \
		sieveHeadMatch(mention_id_list, mention_dict, cluster_dict, cluster_id_list, 3, verbosity)
	if verbosity == 'high':
		print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict) # Print changes
	## more relaxed head matching sieve
	old_mention_dict = copy.deepcopy(mention_dict) # Store to print changes afterwards
	mention_id_list, mention_dict, cluster_dict, cluster_id_list = \
		sieveHeadMatch(mention_id_list, mention_dict, cluster_dict, cluster_id_list, 2, verbosity)
	if verbosity == 'high':		
		print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict) # Print changes
	## most relaxed head matching sieve
	old_mention_dict = copy.deepcopy(mention_dict) # Store to print changes afterwards
	mention_id_list, mention_dict, cluster_dict, cluster_id_list = \
		sieveHeadMatch(mention_id_list, mention_dict, cluster_dict, cluster_id_list, 1, verbosity)
	if verbosity == 'high':		
		print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict)  Print changes		
	## Generate output
	generate_conll(input_file, output_file, doc_tags, sentenceDict, mention_dict)

if __name__ == '__main__':
	# Parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', type=str, help='Path to a file, in .conll format, to be resolved')
	parser.add_argument('output_file', type = str, help = 'The path of where the output should go, e.g. WR77.xml.coref')
	parser.add_argument('--docTags', help = 'If this flag is given, a begin and end document is printed at first and last line of output', dest = 'doc_tags', action = 'store_true')
	args = parser.parse_args()
	main(args.input_file, args.output_file, args.doc_tags, verbosity)

