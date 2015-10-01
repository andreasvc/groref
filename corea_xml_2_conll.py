#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
Script for converting the COREA data in xml format to the conll-format output, preserving all annotation, etc.
Conll-format: http://conll.cemantix.org/2011/data.html
"""

import os, sys, re, argparse, csv
import xml.etree.ElementTree as ET

# Adds token and appropriate id's to tokenArray
def addTokens(text, id_list):
	for token in text.split(' '):
		if token:
			tokenArray.append([token] + id_list)

# Function that recursively goes through markables (mentions)
def processMarkable(parent_markable, id_list):
	if 'id' in parent_markable.attrib: # Check whether actual markable, or sentence
		mention_id = re.findall('[0-9]+', parent_markable.attrib['id'])[0] # Extract mention id
		if 'type' in parent_markable.attrib: # Check whether it is coreferent
			if parent_markable.attrib['type'] in coref_types: # Check for right type of coreference
				ref = parent_markable.attrib['ref']
				if ref != 'empty':
					ref_id = re.findall('[0-9]+', ref)[0]
					coreferential_ids[mention_id] = ref_id
					mention_id = ref_id
		id_list.append(mention_id)
	if parent_markable.text:
		addTokens(parent_markable.text, id_list)		
	if parent_markable.find('markable') is not None: # if it contains other markables
		for child_markable in parent_markable.findall('markable'):
			processMarkable(child_markable, id_list)
	if id_list:
		id_list.pop()
	if parent_markable.tail:
		addTokens(parent_markable.tail, id_list)

# Add round brackets indicating mention begin and end
def postProcessTokenArray(tokenArray, coreferential_ids):
	seenList = []
	for idx, token in enumerate(tokenArray):
		for idx2, mention_id in enumerate(token):
			if idx2 > 0: # Skip first entry, which is the token itself
				if mention_id in coreferential_ids: # Resolve coreferential links, set all mentions that corefer to have same id, that of first mention of the coreference cluster
					while(mention_id in coreferential_ids):
						mention_id = coreferential_ids[mention_id]
					token[idx2] = mention_id
				if mention_id not in seenList: # Check whether needs opening bracket
					token[idx2] = '(' + mention_id
					seenList.append(mention_id)
				if idx != len(tokenArray) - 1: # Check whether needs closing bracket
					if mention_id not in tokenArray[idx+1]:
						token[idx2] += ')'
						seenList.remove(mention_id)
		tokenArray[idx] = [token[0], '|'.join(token[1:])]
	return tokenArray

if __name__ == '__main__':
	# COREA has 4 types of links: bound, bridge, ident(ity) and pred(icate)
	# Types to include in output:
	coref_types = ['ident', 'pred']

	# Parse input argument
	parser = argparse.ArgumentParser()
	parser.add_argument('input_dir', type=str, help='Path to a directory containing XML-files with COREA corpus data')
	parser.add_argument('--printHeader', help= 'If this flag is provided, a header is printed with column names', dest = 'print_header', action = 'store_true')
	args = parser.parse_args()

	# Create output dir
	if not os.path.exists(args.input_dir + '/conll'):
		os.mkdir(args.input_dir + '/conll')
	
	# Process files
	filenames = os.listdir(args.input_dir)
	header = ['doc_id', 'paragraph_id', 'paragraph_sentence_id', 'doc_sentence_id', 'sentence_token_id', 'doc_token_id', 'token', 'coref_id']
	for filename in filenames:
		if re.search('_inline.xml$', filename):
			sys.stdout.write('Processing file: %s\n' % (filename))
			# Parse the xml file
			try: # Empty file in there causes trouble
				tree = ET.parse(args.input_dir + filename) 
			except:
				continue
			root = tree.getroot()
			# Create output file and writer
			conll_file = open(args.input_dir + '/conll/' + filename + '.conll', 'w')
			conll_writer = csv.writer(conll_file,  delimiter = '\t', quoting = csv.QUOTE_NONE, quotechar='')
			if args.print_header:
				conll_writer.writerow(header)
			
			coreferential_ids = {} # dict containing mappings of ids which corefer
			doc_token_id = 0
			doc_sentence_id = 0
			for sentence in root.iter('sentence'):
				tokenArray = [] # Contains extracted tokens and mention_ids
				sentence_token_id = 0
				doc_sentence_id += 1
				alpsent = sentence.attrib['alpsent']
				paragraph_id = re.findall('p.[0-9]+', alpsent)[0][2:] # Extract paragraph number
				sentence_id = re.findall('s.[0-9]+', alpsent)[0][2:] # Extract sentence number
				processMarkable(sentence, []) # Actual processing
				tokenArray.pop() # remove trailing newline
				tokenArray = postProcessTokenArray(tokenArray, coreferential_ids)
				for token in tokenArray:
					sentence_token_id += 1
					doc_token_id += 1
					conll_writer.writerow([filename, paragraph_id, sentence_id, doc_sentence_id, sentence_token_id, doc_token_id, token[0].encode('utf-8')] + token[1:])
				conll_writer.writerow([])
			conll_file.close()
	print 'Done!'
