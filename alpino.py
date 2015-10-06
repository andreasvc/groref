import os
import sys

def parse(xmlFile, dep):
    tmpFile = open('tmp', 'w')
    for line in open(xmlFile, 'r'):
        if len(line) > 1:
            tmpFile.write(line.split('\t')[6] + ' ')
        else:
            tmpFile.write('\n\n')
    tmpFile.close()
    if dep:
        os.system('cat tmp | Alpino number_analyses=1 end_hook=triples -parse > tmp2')
    else:
        os.system('cat tmp | Alpino number_analyses=1 end_hook=syntax -parse > tmp2')

def write(xmlFile, dep):
    if dep:
        parseFile = open(xmlFile + '.dep', 'w')
    else:
        parseFile = open(xmlFile + '.con', 'w')
    sentIdx = 1
    for line in open('tmp2', 'r'):
        if int(line.split('|')[3]) == sentIdx:
            parseFile.write(line)
        else:
            sentIdx += 1
            parseFile.write('\n')
    parseFile.close()

def runAlpino(working):
    tmpPath = 'tmp'
    for xmlFile in os.listdir(working):
        parse(working+xmlFile, True)
        write(working+xmlFile, True)
        parse(working+xmlFile, False)
        write(working+xmlFile, False)
if __name__ == '__main__':
    runAlpino('DCOI/conll/')

