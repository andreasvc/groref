# -*- coding: utf8 -*-
""" Pipeline script that does coreference resolution and evaluation, given
a conll-formatted file or directory containing conll-formatted files. Expects
Alpino parses to be present already. """

from __future__ import absolute_import, division
import os
import re
import argparse
import datetime
import subprocess
import preprocess_clin_data
import coreference_resolution
from utils import (read_number_gender_data, process_and_print_clin_scorer_file,
        allSieves)


def processDocument(filename, verbosity, sieveList, ngdata, timestamp):
    """Do preprocessing, coreference resolution and evaluation for a single
    document."""
    if verbosity != 'none':
        print('processing', filename, '...')
    output_filename = (
        'results/' + timestamp + '/' + filename.split('/')[-1]
    )  # + '.coref'
    scores_filename = output_filename + '.scores'
    if re.search('coref_ne', filename):
        isClinData = True
    else:
        isClinData = False
    if isClinData:
        preprocess_clin_data.preprocess_file(filename)
    with open(scores_filename, 'w') as scores_file:
        if isClinData:
            coreference_resolution.main(
                filename + '.forscorer',
                filename.split('_')[0],
                output_filename,
                True,
                verbosity,
                sieveList,
                ngdata,
            )
            subprocess.call(
                [
                    "conll_scorer/scorer.pl",
                    "all",
                    filename + '.forscorer',
                    output_filename,
                    "none",
                ],
                stdout=scores_file,
            )
        else:
            coreference_resolution.main(
                filename,
                filename.split('_')[0],
                output_filename,
                True,
                verbosity,
                sieveList,
                ngdata,
            )
            subprocess.call(
                [
                    "conll_scorer/scorer.pl",
                    "all",
                    filename,
                    output_filename,
                    "none",
                ],
                stdout=scores_file,
            )


def processDirectory(dirname, verbosity, sieveList, ngdata, timestamp):
    """Do preprocessing, coreference resolution and evaluation for all
    documents in a directory."""
    for filename in os.listdir(dirname):
        if os.path.isfile(os.path.join(dirname, filename)):
            if re.search('.xml.coref_ne$', filename) or re.search(
                '.xml.conll$', filename
            ):
                processDocument(
                    os.path.join(dirname, filename),
                    verbosity,
                    sieveList,
                    ngdata,
                    timestamp)


def postProcessScores(scores_dir, verbosity, onlyTotal=False):
    ''' Aggregates and formats evaluation scores of one or more documents,
	outputs to 'scores_overall'-file
	'''
    # Format: {doc_name: {metric: [Pkey, Ppred, P, Rkey, Rpred, R, F1]} }
    scores = {}
    metric = ''
    for filename in os.listdir(scores_dir):
        if os.path.isfile(os.path.join(scores_dir, filename)) and re.search(
            '.scores$', filename
        ):
            docName = filename.split('_')[0]
            scores[docName] = {
                'muc': [],
                'bcub': [],
                'ceafm': [],
                'ceafe': [],
                'blanc': [],
                'conll': [],
                'md': [],
            }
            for metric in scores[docName]:
                scores[docName][metric] = [0, 1, 0, 0, 1, 0, 0]
            with open(os.path.join(scores_dir, filename), 'r') as scores_file:
                for line in scores_file:
                    if re.search('^METRIC', line):
                        metric = re.split(' ', line)[-1][
                            :-2
                        ]  # Extract metric name
                    if scores[docName]['md'] == [
                        0,
                        1,
                        0,
                        0,
                        1,
                        0,
                        0,
                    ]:  # Avoid filling entry 5 times
                        if re.search('^Identification', line):
                            values = [float(value) for value
                                    in re.findall(r'[0-9]+\.?[0-9]*', line)]
                            scores[docName]['md'] = (
                                values[0:6] + values[7:]
                            )  # At index 6 is the '1' from 'F1', so ignore
                    if metric == 'blanc':
                        if re.search('^BLANC', line):
                            values = [float(value) for value
                                    in re.findall(r'[0-9]+\.?[0-9]*', line)]
                            scores[docName][metric] = values[0:6] + values[7:]
                    else:
                        if re.search('^Coreference:', line):
                            values = [float(value) for value
                                    in re.findall(r'[0-9]+\.?[0-9]*', line)]
                            scores[docName][metric] = values[0:6] + values[7:]
            scores[docName]['conll'] = [
                (
                    scores[docName]['muc'][6]
                    + scores[docName]['bcub'][6]
                    + scores[docName]['ceafe'][6]
                )
                / 3
            ]  # Calculate CoNLL-F1
            # Calculate across-document scores
    totals = {
        'muc': [],
        'bcub': [],
        'ceafm': [],
        'ceafe': [],
        'blanc': [],
        'md': [],
    }
    for metric in totals:
        totals[metric] = [0, 0, 0, 0, 0, 0, 0]
    for document in scores:  # Sum all documents' values
        for metric in scores[document]:
            if metric != 'conll':
                totals[metric] = [
                    val1 + val2
                    for val1, val2 in zip(
                        totals[metric], scores[document][metric]
                    )
                ]
    for metric in totals:
        try:
            totals[metric][2] = totals[metric][0] / totals[metric][1] * 100
        except ZeroDivisionError:
            totals[metric][2] = 0
        try:
            totals[metric][5] = totals[metric][3] / totals[metric][4] * 100
        except ZeroDivisionError:
            totals[metric][5] = 0
        try:
            totals[metric][6] = (
                2
                * totals[metric][2]
                * totals[metric][5]
                / (totals[metric][2] + totals[metric][5])
            )
        except ZeroDivisionError:
            totals[metric][6] = 0
    totals['conll'] = [
        (totals['muc'][6] + totals['bcub'][6] + totals['ceafe'][6]) / 3
    ]

    # 	print scores
    # 	print totals
    # Print scores to screen and file
    with open(scores_dir + '/' + 'scores_overall', 'w') as out_file:
        if verbosity == 'high':
            print('#########################################\nSCORES:')
        else:
            if not onlyTotal:
                print('SCORES:')
        # 		header = 'document name\t\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBCUB-r/p/f1\t\tCEAFM-r/p/f1\t\tCEAFE-r/p/f1\t\tBLANC-r/p/f1\t\tCONLL-f1'
        header = 'document name\t\tMD-r/p/f1\t\tMUC-r/p/f1\t\tBLANC-r/p/f1\t\tCONLL-f1'
        if not onlyTotal:
            print(header)
        out_file.write(header + '\n')
        for document in scores:
            docName = document + (20 - len(document)) * ' '
            a = scores[document]
            # 			scorestring = '%s\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % (docName,  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])
            scorestring = (
                '%s\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f'
                % (
                    docName,
                    a['md'][2],
                    a['md'][5],
                    a['md'][6],
                    a['muc'][2],
                    a['muc'][5],
                    a['muc'][6],
                    a['blanc'][2],
                    a['blanc'][5],
                    a['blanc'][6],
                    a['conll'][0],
                )
            )
            if not onlyTotal:
                print(scorestring)
            out_file.write(scorestring + '\n')
        if verbosity == 'high':
            print('OVERALL:')
        a = totals
        # 		scorestring = '%s\t\t\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f' % ('TOTAL',  a['md'][2],  a['md'][5],  a['md'][6], a['muc'][2], a['muc'][5], a['muc'][6], a['bcub'][2], a['bcub'][5], a['bcub'][6], a['ceafm'][2], a['ceafm'][5], a['ceafm'][6], a['ceafe'][2], a['ceafe'][5], a['ceafe'][6], a['blanc'][2], a['blanc'][5], a['blanc'][6], a['conll'][0])
        scorestring = (
            '%s\t\t\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f/%05.2f/%05.2f\t%05.2f'
            % (
                'TOTAL',
                a['md'][2],
                a['md'][5],
                a['md'][6],
                a['muc'][2],
                a['muc'][5],
                a['muc'][6],
                a['blanc'][2],
                a['blanc'][5],
                a['blanc'][6],
                a['conll'][0],
            )
        )
        print(scorestring)
        out_file.write(scorestring)


def main():
    # Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'target',
            type=str,
            help='Path to a file or directory, in .conll format, '
                'for which to do coreference resolution.')
    parser.add_argument(
            '-v',
            '--verbosity',
            type=str,
            help='Verbosity of output, can be either "high" or "low", '
                'default is "high"',
            default='high')
    parser.add_argument(
            '-s',
            '--sieve',
            help='Given this flag, scores after each sieve are reported',
            dest='per_sieve',
            action='store_true')
    parser.add_argument(
            '-c',
            '--conll',
            help='Given this flag, CoNLL scorer is used',
            dest='conll',
            action='store_true')
    args = parser.parse_args()
    # Put output in timestamped sub-folder of results/
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    print('Timestamp for this run is: %s' % timestamp)
    if args.verbosity == 'high':
        print('Reading in number-gender data...')
    ngdata = read_number_gender_data('ngdata')  # Read in number-gender data
    if args.verbosity == 'high':
        print('Done!')
    os.system('mkdir -p results/' + timestamp)
    if os.path.isdir(args.target):
        if not args.target.endswith('/'):
            args.target += '/'
        if args.per_sieve:
            for i in range(0, len(allSieves) + 1):
                processDirectory(
                        args.target, 'none', allSieves[:i], ngdata, timestamp)
                print('using these sieves: ' + str(allSieves[:i]))
                postProcessScores('results/' + timestamp, 'low', True)
        else:
            # Give range(0,20) as sieveList, so that all sieves are applied
            processDirectory(
                    args.target, args.verbosity, list(range(0, 20)), ngdata,
                    timestamp)
    elif os.path.isfile(args.target):
        if args.per_sieve:
            for i in range(0, len(allSieves)):
                processDocument(
                        args.target, 'none', allSieves[: i + 1], ngdata,
                        timestamp)
                print('using these sieves: ' + str(allSieves[: i + 1]))
                postProcessScores('results/' + timestamp, 'low', True)
        else:
            processDocument(
                    args.target, args.verbosity, list(range(0, 20)), ngdata,
                    timestamp)
    else:
        print('Incorrect input file or directory')
        raise SystemExit
    if not args.per_sieve and args.conll:
        postProcessScores('results/' + timestamp, args.verbosity)
    os.chdir('clin26-eval-master')
    with open('../results/%s/blanc_scores' % timestamp, 'w') as blanc_scores:
        subprocess.call(
            ['bash', 'score_coref.sh', 'coref_ne', 'dev_corpora/coref_ne',
                '../results/' + timestamp, 'blanc'],
            stdout=blanc_scores)
    os.chdir('../')
    process_and_print_clin_scorer_file(os.path.join(
            'results', timestamp, 'blanc_scores'))
    print('Timestamp for this run was: %s' % timestamp)


if __name__ == '__main__':
    main()
