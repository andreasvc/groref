import os
import sys

def parse(conllFile, tokenIdx, nameCut):
    tmpFile = open('tmp', 'w')
    for line in open(conllFile, 'r'):
        if line.startswith('doc_id'):
            pass
        else:
            if len(line.split('\t')) > 1:
                tmpFile.write(line.split('\t')[tokenIdx] + ' ')
            else:
                tmpFile.write('\n\n')
    tmpFile.close()
    
    folder = conllFile[:conllFile.find('_')]
    print(folder)
    os.mkdir(folder)
    
    os.system('cat tmp | Alpino number_analyses=1 end_hook=xml -flag treebank ' + folder + ' -parse')

def runAlpino(working, tokenIdx, nameCut):
    tmpPath = 'tmp'
    for conllFile in os.listdir(working):
        parse(working+conllFile, tokenIdx, nameCut)

if __name__ == '__main__':
    #runAlpino('DCOI/conll/', 6, 30)
    #runAlpino('clinDevData/', 1, 21)

