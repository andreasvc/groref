#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Pipeline script that does coreference resolution and evaluation, given
a conll-formatted file or directory containing conll-formatted files. Expects
Alpino parses to be present already. """

import argparse, os, re, subprocess, datetime

import preprocess_clin_data
import coreference_resolution

def processDocument(filename):
	''' Do preprocessing, coreference resolution and evaluation for a single 
	document.
	'''
	global timestamp
	print 'processing ' + filename + '...'
	output_filename = 'results/' + timestamp + '/' + filename.split('/')[-1] + '.coref'
	scores_filename = output_filename + '.scores'
	if re.search('coref_ne', filename):
		isClinData = True
	else:
		isClinData = False
	if isClinData:
		preprocess_clin_data.preprocess_file(filename)
	coreference_resolution.main(filename, output_filename, True)
	with open(scores_filename, 'w') as scores_file:
		if isClinData:
			subprocess.call(["conll_scorer/scorer.pl", "all", filename + '.forscorer', output_filename, "none"], stdout = scores_file)
		else:
			subprocess.call(["conll_scorer/scorer.pl", "all", filename, output_filename, "none"], stdout = scores_file)
		
def processDirectory(dirname):
	'''Do preprocessing, coreference resolution and evaluation for all 
	documents in a directory.
	'''
	for filename in os.listdir(dirname):
		if os.path.isfile(dirname + filename):
			if re.search('.xml.coref_ne$', filename) or re.search('.xml.conll$', filename):
				processDocument(dirname + filename)

if __name__ == '__main__':
	# Parse input arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('target', type=str, help='Path to a file or directory, in .conll format, for which to do coreference resolution.')
	args = parser.parse_args()
	# Put output in timestamped sub-folder of results/
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
	print 'Timestamp for this run is: %s' % timestamp
	if not 'results' in os.listdir('./'):
	    os.system('mkdir results/')
	if not timestamp in os.listdir('results/'):
		os.system('mkdir results/' + timestamp)
	
	if os.path.isdir(args.target):
		processDirectory(args.target)
	elif os.path.isfile(args.target):
		processDocument(args.target)
	else:
		print 'Incorrect input file or directory'
		raise SystemExit
	print 'Timestamp for this run was: %s' % timestamp

	
