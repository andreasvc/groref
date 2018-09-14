# -*- coding: utf8 -*-
"""Script for converting the COREA data in xml format to the conll-format
output, preserving all annotation, etc.
Conll-format: http://conll.cemantix.org/2011/data.html"""

import os
import re
import sys
import csv
import argparse
import xml.etree.ElementTree as ET


# COREA has 4 types of links: bound, bridge, ident(ity) and pred(icate)
# Types to include in output:
coref_types = ['ident', 'pred']


def addTokens(text, id_list, tokenArray):
    """Adds token and appropriate IDs to tokenArray"""
    for token in text.split(' '):
        if token:
            tokenArray.append([token] + id_list)


def processMarkable(parent_markable, id_list, tokenArray, coreferential_ids):
    """Function that recursively goes through markables (mentions)"""
    # Check whether actual markable, or sentence
    if 'id' in parent_markable.attrib:
        # Extract mention id
        mention_id = re.findall('[0-9]+', parent_markable.attrib['id'])[0]
        if 'type' in parent_markable.attrib:  # Check whether it is coreferent
            # Check for right type of coreference
            if (parent_markable.attrib['type'] in coref_types
                and 'ref' in parent_markable.attrib):
                ref = parent_markable.attrib['ref']
                if ref != 'empty':
                    ref_id = re.findall('[0-9]+', ref)[0]
                    coreferential_ids[mention_id] = ref_id
                    mention_id = ref_id
        id_list.append(mention_id)
    if parent_markable.text:
        addTokens(parent_markable.text, id_list, tokenArray)
    # if it contains other markables
    if parent_markable.find('markable') is not None:
        for child_markable in parent_markable.findall('markable'):
            processMarkable(
                    child_markable, id_list, tokenArray, coreferential_ids)
    if id_list:
        id_list.pop()
    if parent_markable.tail:
        addTokens(parent_markable.tail, id_list, tokenArray)


def postProcessTokenArray(tokenArray, coreferential_ids, no_inner=False):
    """Add round brackets indicating mention begin and end"""
    seenList = []
    for idx, token in enumerate(tokenArray):
        for idx2, mention_id in enumerate(token):
            if idx2 > 0:  # Skip first entry, which is the token itself
                original_mention_ids = []
                # Resolve coreferential links, set all mentions that corefer to
                # have same id, that of first mention of the coreference
                # cluster
                if mention_id in coreferential_ids:
                    if (coreferential_ids.get(coreferential_ids[mention_id])
                            == mention_id):
                        # raise ValueError('coref cycle')
                        print('coref cycle')
                        coreferential_ids.pop(mention_id)
                    while mention_id in coreferential_ids:
                        # Keep this to check for closing bracket
                        original_mention_ids.append(mention_id)
                        mention_id = coreferential_ids[mention_id]
                    token[idx2] = mention_id
                # Check whether needs opening bracket
                if mention_id not in seenList:
                    token[idx2] = '(' + mention_id
                    seenList.append(mention_id)
                # Check whether needs closing bracket
                if idx != len(tokenArray) - 1:
                    if (mention_id not in tokenArray[idx + 1][1:]
                            and not set(original_mention_ids).intersection(
                                set(tokenArray[idx + 1][1:]))):
                        token[idx2] += ')'
                        seenList.remove(mention_id)
                else:
                    token[idx2] += ')'
                    seenList.remove(mention_id)
        if len(token) == 1:  # Add dash for tokens not part of a mention
            token.append('-')
        tokenArray[idx] = [token[0], '|'.join(token[1:])]
    return tokenArray


def removeDuplicates(tokenArray, filename):
    """Function to remove mentions that have exact same span. Sometimes these
    are annotated that way in COREA and this causes trouble with the scorer. No
    nice way to do automatically,  so do it with ugly per-document per-mention
    rules"""
    if filename == 'WR-P-P-H-0000000077_inline.xml':
        for token in tokenArray:
            if token[0] != '134' and '134' in token[1:]:
                token.remove('134')
    return tokenArray


def main():
    # Parse input argument
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'input_dir', type=str,
            help='Path to a directory containing XML-files '
                'with COREA corpus data')
    parser.add_argument(
            '--noInner', dest='no_inner', action='store_true',
            help='If this flag is given, corefIDs are only printed for first '
                'and last word of mention')
    parser.add_argument(
            '--docTags', dest='doc_tags', action='store_true',
            help='If this flag is given, a begin and end document is printed '
                'at first and last line of output')
    parser.add_argument(
            '--printHeader', dest='print_header', action='store_true',
            help='If this flag is provided, a header is printed '
                'with column names')
    args = parser.parse_args()

    # Create output dir
    if not os.path.exists(args.input_dir + '/conll'):
        os.mkdir(args.input_dir + '/conll')

    # Process files
    filenames = os.listdir(args.input_dir)
    header = ['doc_id', 'paragraph_id', 'paragraph_sentence_id',
            'doc_sentence_id', 'sentence_token_id', 'doc_token_id', 'token',
            'coref_id']
    for filename in filenames:
        if re.search('_inline.xml$', filename):
            sys.stdout.write('Processing file: %s\n' % (filename))
            # Parse the xml file
            try:  # Empty file in there causes trouble
                tree = ET.parse(args.input_dir + '/' + filename)
            except Exception as err:
                print('Processing error', filename, err)
                continue
            root = tree.getroot()
            # Create output file and writer
            conll_file = open(
                    args.input_dir + '/conll/' + filename + '.conll', 'w')
            conll_writer = csv.writer(
                    conll_file, delimiter='\t',
                    quoting=csv.QUOTE_NONE, quotechar='')
            if args.print_header:
                conll_writer.writerow(header)
            docName = filename.split('_')[0]
            if args.doc_tags:
                conll_writer.writerow(
                        ['#begin document (' + docName + '); part 000'])

            # dict containing mappings of ids which corefer
            coreferential_ids = {}
            doc_token_id = 0
            doc_sentence_id = 0
            for sentence in root.iter('sentence'):
                tokenArray = []  # Contains extracted tokens and mention_ids
                sentence_token_id = 0
                doc_sentence_id += 1
                try:
                    alpsent = sentence.attrib['alpsent']
                    # Extract paragraph number
                    paragraph_id = re.findall('p.[0-9]+', alpsent)[0][2:]
                    # Extract sentence number
                    sentence_id = re.findall('s.[0-9]+', alpsent)[0][2:]
                except IndexError:
                    paragraph_id = '-1'
                    sentence_id = '-1'
                # Actual processing
                processMarkable(sentence, [], tokenArray, coreferential_ids)
                tokenArray.pop()  # remove trailing newline
                tokenArray = removeDuplicates(tokenArray, filename)
                tokenArray = postProcessTokenArray(
                        tokenArray, coreferential_ids)
                for token in tokenArray:
                    sentence_token_id += 1
                    doc_token_id += 1
                    # Do not print cluster IDs except for at start and end of
                    # mention
                    if args.no_inner:
                        new_IDs = []
                        for old_ID in token[1].split('|'):
                            # Check for brackets
                            if '(' in old_ID or ')' in old_ID:
                                new_IDs.append(old_ID)
                        token[1] = '|'.join(new_IDs)
                        if not new_IDs:  # If empty
                            token[1] = '-'
                    conll_writer.writerow(
                            [docName, paragraph_id, sentence_id,
                                doc_sentence_id, sentence_token_id,
                                doc_token_id, token[0]]
                            + token[1:])
                conll_writer.writerow([])
            if args.doc_tags:
                conll_writer.writerow(['#end document'])
            conll_file.close()
    print('Done!')


if __name__ == '__main__':
    main()
