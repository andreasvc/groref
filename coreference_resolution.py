#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Entity coreference resolution system for the CLIN26 Shared Task.
Based on the Stanford Coreference Resolution system. Requires CoNLL-formatted
input data and Alpino pars in xml as input, gives CoNLL-formatted output. """

import os, argparse, re, sys, copy
import xml.etree.ElementTree as ET
from utils import *
from sieveDummy import sieveDummy
from sieveHeadMatch1 import sieveHeadMatch1

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
		self.head_begin = 0
		self.head_end = 0
		self.headWords = []
		self.attribs = {}
		
# Class for 'cluster'-objects
class Cluster:
	'Class of clusters, which contain features, an ID and a list of member-mentions-IDs'
	def __init__(self, clusterID):
		self.ID = clusterID
		self.mentionList = []

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
def make_mention(mention_node, mention_type, sentNum):
	global mentionID
	new_ment = Mention(mentionID)
	mentionID += 1
	new_ment.type = mention_type
	new_ment.begin = int(mention_node.attrib["begin"])
	new_ment.end = int(mention_node.attrib["end"])
	new_ment.numTokens = new_ment.end - new_ment.begin
	new_ment.sentNum = sentNum
	new_ment.attribs = mention_node.attrib
	for node in mention_node.iter():
		if "word" in node.attrib:
			new_ment.tokenList.append(node.attrib["word"])
	if mention_type.lower()[:2] == 'np':
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
def detect_mentions(conll_list, tree_list, docFilename, verbosity):
	global mentionID, sentenceDict
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
				mention_list.append(make_mention(mention_node, name, sentNum))
		
		mwu_rels = ['obj1','su','cnj'] #hd 14/65 
		for mention_node in tree.findall(".//node[@cat='mwu']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
				name = 'mwu_' + mention_node.attrib['rel']
				mention_list.append(make_mention(mention_node, 'mwu', sentNum))

		for mention_node in tree.findall(".//node"):
			if 'cat' not in mention_node.attrib and mention_node.attrib['rel'] == 'su':
				mention_list.append(make_mention(mention_node, 'su', sentNum))
		
		for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
			mention_list.append(make_mention(mention_node, 'noun', sentNum))
	
		for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
			mention_list.append(make_mention(mention_node, 'Pronoun', sentNum))

		# Take all name elements, some of which might be parts of same name. Those are stitched together later.
		for mention_node in tree.findall(".//node[@pos='name']"):
			mention_list.append(make_mention(mention_node, 'Name', sentNum))
	
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

# Human-readable printing of the output of the mention detection sieve	
def print_mentions_inline(sentenceDict):
	for sentNum in sentenceDict:
		sentLength = len(sentenceDict[sentNum].split(' '))
		closingBrackets = '' # Print closing brackets for mention that close at end of sentence
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention_id in mention_id_list:
				mention = mention_dict[mention_id]
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print colour_text('[', 'red'),
#						sys.stdout.write(colour_text('[', 'red'))						
					if mention.end == idx:
						print colour_text(']', 'red'),
#						sys.stdout.write(colour_text(']', 'red'))
					if idx + 1 == sentLength and mention.end == sentLength:
						closingBrackets += '] '
			print colour_text(token.encode('utf-8'), 'white'),
			print colour_text(closingBrackets, 'red'),
		print ''
		
# Human-readable printing of a comparison between the output of the mention detection sieve	and the 'gold' standard
# Green brackets are correct, gold/orange brackets are mention boundaries only found in the gold standard, and
# red brackets are only found in our output
def print_mention_analysis_inline(conll_list):
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
		
# Creates a cluster for each mention, fills in features
def initialize_clusters():
	cluster_id_list = []
	cluster_dict = {}
	for mention_id, mention in mention_dict.iteritems():
		new_cluster = Cluster(mention.ID) # Initialize with same ID as initial mention
		new_cluster.mentionList.append(mention.ID)
		mention.clusterID = new_cluster.ID
		cluster_dict[new_cluster.ID] = new_cluster
		cluster_id_list.append(new_cluster.ID)
	return cluster_dict, cluster_id_list
	
# Creates conll-formatted output with the clustering information
def generate_conll(docName, output_filename, doc_tags):
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
	global mentionID, mention_id_list, sentenceDict, cluster_dict, mention_dict, cluster_id_list
	mentionID = 0 # Initialize mentionID
	sentenceDict = {} # Initialize dictionary containing sentence strings
	# Do mention detection, give back 3 global variables:
	## mention_id_list contains list of mention IDs in right order, for traversing in sieves
	## mention_dict contains the actual mentions, format: {id: Mention}
	## cluster_dict contains all clusters, in a dict
	mention_id_list, mention_dict = detect_mentions(conll_list, xml_tree_list, input_file, verbosity)
	if verbosity == 'high':
		print 'OUR MENTION OUTPUT:'
		print_mentions_inline(sentenceDict)
		print 'MENTION DETECTION OUTPUT VS. GOLD STANDARD:'
		print_mention_analysis_inline(conll_list)								
	cluster_dict, cluster_id_list = initialize_clusters()
	## APPLY SIEVES HERE
	# Apply dummy sieve, naming is reversed so all sieve function can start with sieve :)
#	mention_id_list, mention_dict, cluster_dict, cluster_id_list = \
#		sieveDummy(mention_id_list, mention_dict, cluster_dict, cluster_id_list)
	old_mention_dict = copy.deepcopy(mention_dict) # Store to print changes afterwards
	mention_id_list, mention_dict, cluster_dict, cluster_id_list = \
		sieveHeadMatch1(mention_id_list, mention_dict, cluster_dict, cluster_id_list)
	print_linked_mentions(old_mention_dict, mention_id_list, mention_dict, sentenceDict) # Print changes
	##
	# Generate output
	generate_conll(input_file, output_file, doc_tags)

if __name__ == '__main__':
	# Parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', type=str, help='Path to a file, in .conll format, to be resolved')
	parser.add_argument('output_file', type = str, help = 'The path of where the output should go, e.g. WR77.xml.coref')
	parser.add_argument('--docTags', help = 'If this flag is given, a begin and end document is printed at first and last line of output', dest = 'doc_tags', action = 'store_true')
	args = parser.parse_args()
	main(args.input_file, args.output_file, args.doc_tags, verbosity)

