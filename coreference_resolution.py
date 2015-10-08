#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Entity coreference resolution system for the CLIN26 Shared Task.
Based on the Stanford Coreference Resolution system. Requires CoNLL-formatted
input data and Alpino pars in xml as input, gives CoNLL-formatted output. """

import os, argparse, re, sys
import xml.etree.ElementTree as ET

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
		
# Class for 'cluster'-objects
class Cluster:
	'Class of clusters, which contain features, an ID and a list of member-mentions-IDs'
	def __init__(self, clusterID):
		self.ID = clusterID
		self.mentionList = []

# Read in conll file, return list of lists containing a single word + annotation
def read_conll_file(fname):
	conll_list = []
	for line in open(fname, 'r'):
		split_line = line.strip().split('\t')
		if len(split_line) > 1:
			if split_line[0] != 'doc_id' and line[0] != '#': # Skip header and/or document tags
				conll_list.append(split_line)
	return conll_list
	
# Read in xml-files containing parses for sentences in document, return list of per-sentence XML trees
def read_xml_parse_files(fname):
	xml_tree_list = []
	print fname
	dir_name = '/'.join(fname.split('/')[0:-1]) + '/' + fname.split('/')[-1].split('_')[0] + '/'
	xml_file_list = os.listdir(dir_name)
	for xml_file in sorted(xml_file_list):
		if re.search('[0-9].xml', xml_file):
			try:
				tree = ET.parse(dir_name + xml_file)
			except IOError:
				print 'Parse file not found: %s' % (xml_file)
		xml_tree_list.append(tree)
	return xml_tree_list

# Stitch multi-word name mentions together
def stitch_names(mention_list):
	stitched_mention_list = []
	idx = 0
	# Assume all split names are sequential in mention_list
	while idx < len(mention_list): 
		if mention_list[idx].type == 'Name': # Ignore non-names
			inc = 1 # How far to search ahead
			continueSearch = True
			while continueSearch:
				if idx + inc < len(mention_list):
					# Mentions should be part of same sentence
					if mention_list[idx + inc].begin == mention_list[idx].end and mention_list[idx + inc].sentNum == mention_list[idx].sentNum:
						mention_list[idx].end = mention_list[idx + inc].end
						mention_list[idx].numTokens += mention_list[idx + inc].numTokens
						mention_list[idx].tokenList += mention_list[idx + inc].tokenList
						inc += 1 # Stitched one part to the current mention, now check the mention after that
					else:
						continueSearch = False
				else:
					continueSearch = False
			stitched_mention_list.append(mention_list[idx])
			idx += inc # If 3 parts stitched together, skip the subsequent 2 mentions
		else:
			stitched_mention_list.append(mention_list[idx])
			idx += 1
	return stitched_mention_list
	
# Sort mentions in list by sentNum, begin, end
def sort_mentions(mention_list):
	return sorted(mention_list, key = lambda x: (x.sentNum, x.begin, x.end))

# Mention detection sieve, selects all NPs, pronouns, names		
def detect_mentions(conll_list, tree_list, docFilename):
	global mentionID, sentenceDict
	mention_list = []
	for tree in tree_list:
		sentNum = tree.find('comments').find('comment').text
		sentNum = re.findall('#[0-9]+', sentNum)[0][1:]
		# Extract mentions (NPs, pronouns, names)
		print 'Detecting mentions in sentence number %s,' % (sentNum),
		sentenceDict[int(sentNum)] = tree.find('sentence').text
		np_list = tree.findall(".//node[@cat='np']")
		print 'found %d NPs, ' % len(np_list),
		pron_list = tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']")
		print '%d (possessive) pronouns, ' % len(pron_list),
		# Take all name elements, some of which might be parts of same name. Those are stitched together later.
		name_list = tree.findall(".//node[@pos='name']") 
		print 'and %d (parts of) names.' % len(name_list)
		# Create Mention objects and fill in properties
		for mention_node in np_list + pron_list + name_list:
			new_ment = Mention(mentionID)
			mentionID += 1
			new_ment.sentNum = int(sentNum)
			new_ment.begin = int(mention_node.attrib["begin"])
			new_ment.end = int(mention_node.attrib["end"])
			new_ment.numTokens = new_ment.end - new_ment.begin
			for node in mention_node.iter():
				if "word" in node.attrib:
					new_ment.tokenList.append(node.attrib["word"])
			if mention_node in np_list:
				new_ment.type = 'NP'
			elif mention_node in pron_list:
				new_ment.type = 'Pronoun'
			else:
				new_ment.type = 'Name'
			mention_list.append(new_ment)
	# Stitch together split name-type mentions
	mention_list = stitch_names(mention_list)
	# Sort list properly
	mention_list = sort_mentions(mention_list)
	return mention_list

# Human-readable printing of the output of the mention detection sieve	
def print_mentions_inline(sentenceDict, mention_list):
	for sentNum in sentenceDict:
		for idx, token in enumerate(sentenceDict[sentNum].split(' ')):
			for mention in mention_list:
				if mention.sentNum == sentNum:
					if mention.begin == idx:
						print '[',
					if mention.end == idx:
						print ']',
			print token,
		print ''

# Creates a cluster for each mention, fills in features
def initialize_clusters(mention_list):
	cluster_list = []
	for mention in mention_list:
		new_cluster = Cluster(mention.ID) # Initialize with same ID as initial mention
		new_cluster.mentionList.append(mention.ID)
		mention.clusterID = new_cluster.ID
		cluster_list.append(new_cluster)
	return cluster_list
	
# Creates conll-formatted output with the clustering information
def generate_conll(sentenceDict, docName, mention_list, output_filename, doc_tags):
	output_file = open(output_filename, 'w')
	docName = docName.split('/')[-1].split('_')[0]
	if doc_tags:
		output_file.write('#begin document (' + docName + '); part 000\n')	
	for key in sorted(sentenceDict.keys()): # Cycle through sentences
		for token_idx, token in enumerate(sentenceDict[key].split(' ')): # Cycle through words in sentences
			corefLabel = ''
			for mention in mention_list: # Check all mentions, to see whether token is part of mention
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

# Function that takes two mentions, and merges the clusters they are part of
def mergeClustersByMentions(mention1, mention2):
	global cluster_list, mention_list
	if mention1.clusterID == mention2.clusterID: # Cannot merge if mentions are part of same cluster
		return
	for idx, cluster in enumerate(cluster_list): # Find clusters by ID, could be more efficient
		if mention1.clusterID == cluster.ID:
			cluster1 = cluster
		if mention2.clusterID == cluster.ID:
			cluster2 = cluster
			cluster2_idx = idx
	# Put all mentions of cluster2 in cluster1
	for mentionID in cluster2.mentionList:
		cluster1.mentionList.append(mentionID)
		for mention in mention_list:
			if mention.ID == mentionID:
				mention.clusterID = cluster1.ID
	del cluster_list[cluster2_idx]
	

# Dummy sieve that links each second mention to the preceding mention, for testing purposes (output/evaluation)
def sieveDummy():
	global mention_list, cluster_list
	for idx, mention in enumerate(mention_list):
		if idx % 3 == 1:
			mergeClustersByMentions(mention, mention_list[idx-2])

def main(input_file, output_file, doc_tags):
	# Read input files
	try:
		conll_list = read_conll_file(input_file)
	except IOError:
		print 'CoNLL input file not found: %s' % (input_file)
	xml_tree_list = read_xml_parse_files(input_file)
	print 'Number of xml parse trees found: %d' % (len(xml_tree_list))
	global mentionID, mention_list, sentenceDict, cluster_list
	mentionID = 0 # Initialize mentionID
	sentenceDict = {} # Initialize dictionary containing sentence strings
	# TODO: Change mention_list to a dictionary, to be able to find mentions by ID? (same goes for clusters)
	# Do mention detection
	mention_list = detect_mentions(conll_list, xml_tree_list, input_file)
	print_mentions_inline(sentenceDict, mention_list)		
	cluster_list = initialize_clusters(mention_list)
	# Do coreference resolution
	sieveDummy() # Apply dummy sieve
	# Generate output
	generate_conll(sentenceDict, input_file, mention_list, output_file, doc_tags)	

if __name__ == '__main__':
	# Parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', type=str, help='Path to a file, in .conll format, with .dep and .con parse, to be resolved')
	parser.add_argument('output_file', type = str, help = 'The path of where the output should go, e.g. WR77.xml.coref')
	parser.add_argument('--docTags', help = 'If this flag is given, a begin and end document is printed at first and last line of output', dest = 'doc_tags', action = 'store_true')
	args = parser.parse_args()
	main(args.input_file, args.output_file, args.doc_tags)

