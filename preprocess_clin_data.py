#!/usr/bin/env python
# -*- coding: utf8 -*-

""" Script for simple conversion of CLIN data to a format
that can be used by the scorer. I.e., adding document tags
and columns. """

def preprocess_file(filename):
	'''
	Takes one CLIN data file, outputs same file, with .forscorer appended
	to filename. Adds document tags, document name per-line and dummy columns.
	'''
	input_file = open(filename, 'r')
	output_file = open(filename + '.forscorer', 'w')
	docName = filename.split('/')[-1].split('_')[0]
	output_file.write('#begin document (' + docName + '); part 000\n') # Add in document tags
	for line in input_file:
		output_file.write(docName + '\t' + '0\t'*4) # Add in document name and dummy columns
		output_file.write(line)
	output_file.write('#end document')  # Add in document tags

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', type=str, help='Path to a file from the CLIN data to be processed for scoring.')
	args = parser.parse_args()
	preprocess_file(args.input_file)

