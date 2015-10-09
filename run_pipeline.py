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
#	coreference_resolution.main(filename, output_filename, True)
	with open(scores_filename, 'w') as scores_file:
		if isClinData:
			coreference_resolution.main(filename + '.forscorer', output_filename, True)
			subprocess.call(["conll_scorer/scorer.pl", "all", filename + '.forscorer', output_filename, "none"], stdout = scores_file)
		else:
			coreference_resolution.main(filename, output_filename, True)
			subprocess.call(["conll_scorer/scorer.pl", "all", filename, output_filename, "none"], stdout = scores_file)
		
def processDirectory(dirname):
	'''Do preprocessing, coreference resolution and evaluation for all 
	documents in a directory.
	'''
	for filename in os.listdir(dirname):
		if os.path.isfile(dirname + filename):
			if re.search('.xml.coref_ne$', filename) or re.search('.xml.conll$', filename):
				processDocument(dirname + filename)
				
def postProcessScores(scores_dir):
	''' Aggregates and formats evaluation scores of one or more documents,
	outputs to 'scores_overall'-file
	'''
	scores = {} # Format: {doc_name: {metric: [Pkey, Ppred, P, Rkey, Rpred, R, F1]} }
	metric = ''
	for filename in os.listdir(scores_dir):
		if os.path.isfile(scores_dir + '/' + filename) and re.search('.scores$', filename):
			docName = filename.split('_')[0]
			scores[docName] = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'conll' : [], 'md' : []}
			for metric in scores[docName]:
				scores[docName][metric] = [0, 1, 0, 0, 1, 0, 0]
			with open(scores_dir + '/' + filename, 'r') as scores_file:
				for line in scores_file:
					if re.search('^METRIC', line):
						metric = re.split(' ', line)[-1][:-2] # Extract metric name
					if scores[docName]['md'] == [0, 1, 0, 0, 1, 0, 0]: # Avoid filling entry 5 times
						if re.search('^Identification', line):
							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
							scores[docName]['md'] = values[0:6] + values[7:] # At index 6 is the '1' from 'F1', so ignore
					if metric == 'blanc':
						if re.search('^BLANC', line):
							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
							scores[docName][metric] = values[0:6] + values[7:]
					else:
						if re.search('^Coreference:', line):
							values = [float(value) for value in re.findall('[0-9]+\.?[0-9]*', line)]
							scores[docName][metric] = values[0:6] + values[7:]
			scores[docName]['conll'] = [(scores[docName]['muc'][6] + scores[docName]['bcub'][6] + scores[docName]['ceafe'][6]) / 3] # Calculate CoNLL-F1
	# Calculate across-document scores
	totals = {'muc' : [], 'bcub' : [], 'ceafm' : [], 'ceafe' : [], 'blanc' : [], 'md' : []}
	for metric in totals:
		totals[metric] = [0, 0, 0, 0, 0, 0, 0]
	for document in scores: # Sum all documents' values
		for metric in scores[document]:
			if metric != 'conll':
				totals[metric] = [val1 + val2 for val1, val2 in zip(totals[metric], scores[document][metric])]
	print scores
	print totals
	for metric in totals:
		totals[metric][2] = totals[metric][0] / totals[metric][1] * 100
		totals[metric][5] = totals[metric][3] / totals[metric][4] * 100
		try:
			totals[metric][6] = 2 * totals[metric][2] * totals[metric][5] / (totals[metric][2] + totals[metric][5])
		except ZeroDivisionError:
			totals[metric][6] = 0
	totals['conll'] = [(totals['muc'][6] + totals['bcub'][6] + totals['ceafe'][6] ) / 3]
	# Print scores to screen and file
	with open(scores_dir + '/' + 'scores_overall', 'w') as out_file:
		print '#########################################\nSCORES:'
		header = 'document name\t\tMD-p/r/f1\t\tMUC-p/r/f1\t\tBCUB-p/r/f1\t\tCEAFM-p/r/f1\t\tCEAFE-p/r/f1\t\tBLANC-p/r/f1\t\tCONLL-f1'
		print header
		out_file.write(header + '\n')

		for document in scores:
			a = scores[document]
			scorestring = '%s\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % (document,  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])
			print scorestring
			out_file.write(scorestring + '\n')
		print '##OVERALL:##'
		a = totals
		scorestring = '%s\t\t\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % ('TOTAL',  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])
		print scorestring
		out_file.write(scorestring)
	
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
		args.target += '/'
		processDirectory(args.target)
	elif os.path.isfile(args.target):
		processDocument(args.target)
	else:
		print 'Incorrect input file or directory'
		raise SystemExit
	postProcessScores('results/' + timestamp)
	print 'Timestamp for this run was: %s' % timestamp

	
