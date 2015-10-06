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
		self.docName = ''
		self.sentNum = 0
		self.tokenList = []
		self.numTokens = 0
		self.begin = 0 # Token ID of first token
		self.end = 0 # Token ID of last token + 1
		self.type = '' # Pronoun, NP or Name

# Read in conll file, return list of lists containing a single word + annotation
def read_conll_file(fname):
	conll_list = []
	for line in open(fname, 'r'):
		split_line = line.strip().split('\t')
		if len(split_line) > 1:
			if split_line[0] != 'doc_id': # Skip header
				conll_list.append(split_line)
	return conll_list
	
# Read in xml-files containing parses for sentences in document, return list of per-sentence XML trees
def read_xml_parse_files(fname):
	xml_tree_list = []
	dir_name = fname[:-17] + '/'
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
	
# Mention detection sieve, selects all NPs, pronouns, names		
def detect_mentions(conll_list, tree_list, docFilename):
	global mentionID, sentenceDict
	mention_list = []
	docName = re.split('/', docFilename)[-1][:-17]
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
			new_ment.docName = docName
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
	return mention_list
	
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
	
if __name__ == '__main__':
	# Parse input argument
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', type=str, help='Path to a file, in .conll format, with .dep and .con parse, to be resolved')
	args = parser.parse_args()
	# Read input files
	try:
		conll_list = read_conll_file(args.input_file)
	except IOError:
		print 'CoNLL input file not found: %s' % (args.input_file)
	xml_tree_list = read_xml_parse_files(args.input_file)
	print 'Number of xml parse trees found: %d' % (len(xml_tree_list))
	mentionID = 0 # Initialize mentionID
	sentenceDict = {} # Initialize dictionary containing sentence strings
	mention_list = detect_mentions(conll_list, xml_tree_list, args.input_file)
	print_mentions_inline(sentenceDict, mention_list)		
	
	
	
