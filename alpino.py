import os
import sys

def parse(xmlFile):
    tmpFile = open('tmp', 'w')
    for line in open(xmlFile, 'r'):
        if len(line) > 1:
            tmpFile.write(line.split('\t')[6] + ' ')
        else:
            tmpFile.write('\n\n')
    tmpFile.close()
    
    folder = xmlFile[:30]
    print(folder)
    os.mkdir(folder)
    
    os.system('cat tmp | Alpino number_analyses=1 end_hook=xml -flag treebank ' + folder + ' -parse')

def runAlpino(working):
    tmpPath = 'tmp'
    for xmlFile in os.listdir(working):
        parse(working+xmlFile)

if __name__ == '__main__':
    runAlpino('DCOI/conll/')

