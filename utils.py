#!/usr/bin/env python

import colorama as c
import re, sys, os
import xml.etree.ElementTree as ET

### GLOBAL VARIABLES ###

# List of Dutch Stop words (http://www.ranks.nl/stopwords/dutch)
stopWords = ['aan', 'af', 'al', 'als', 'bij', 'dan', 'dat', 'die', 'dit', 'een', 'en', 'er', 'had', 'heb', 'hem', 'het', 'hij', 'hoe', 'hun', 'ik ', 'in', 'is', 'je', 'kan', 'me', 'men', 'met', 'mij', 'nog', 'nu', 'of', 'ons', 'ook', 'te', 'tot', 'uit', 'van', 'was ', 'wat', 'we', 'wel', 'wij', 'zal', 'ze', 'zei', 'zij', 'zo', 'zou']

# First available mentionID
mentionID = 0 

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

### SIEVE HELPERS ###

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
