# -*- coding: utf8 -*-
'''Mention detection sieve of the coreference resolution system'''

from itertools import count
from utils import add_mention, make_mention, stitch_names, sort_mentions


def allWordsHaveAlpha(wordList):
    for word in wordList:
        if not any(c.isalpha() for c in word):
            return False
    return True


def handleComma(new_mention, tree, sentNum, ngdata, mention_list, mentionID):
    if new_mention.tokenList[1] == ',' and len(new_mention.tokenList) > 3:
        add_mention(mention_list, new_mention)
    elif (
        len(new_mention.tokenList) == 3
        and new_mention.tokenList[1] == ','
        and 'neclass' in new_mention.tokenAttribs[0]
        and new_mention.tokenAttribs[0]['neclass'] == 'LOC'
    ):
        add_mention(mention_list, new_mention)
        new_mention1 = make_mention(
            new_mention.tokenList.index(',') + new_mention.begin + 1,
            new_mention.end,
            tree,
            'np_comma',
            sentNum,
            next(mentionID),
            ngdata,
        )
        add_mention(mention_list, new_mention)
    else:
        new_mention1 = make_mention(
            new_mention.begin,
            new_mention.begin + new_mention.tokenList.index(','),
            tree,
            'np_comma',
            sentNum,
            next(mentionID),
            ngdata,
        )
        new_mention2 = make_mention(
            new_mention.tokenList.index(',') + new_mention.begin + 1,
            new_mention.end,
            tree,
            'np_comma',
            sentNum,
            next(mentionID),
            ngdata,
        )
        add_mention(mention_list, new_mention1)
        add_mention(mention_list, new_mention2)


# 28.96/50.84/36.90
# 27.36/52.94/36.08 na allWordsHaveAlpha
# 24.80/58.00/34/80 na extra if for firstChild
def findNP(tree, sentNum, ngdata, mention_list, mentionID):
    np_rels = ['su', 'app', 'body', 'sat', 'predc', 'obj1', 'cnj']
    for mention_node in tree.findall(".//node[@cat='np']"):
        len_ment = int(mention_node.attrib['end']) - int(
            mention_node.attrib['begin']
        )
        if mention_node.attrib['rel'] in np_rels and len_ment < 7:
            name = 'np_' + mention_node.attrib['rel']
            new_mention = make_mention(
                mention_node.attrib['begin'],
                mention_node.attrib['end'],
                tree,
                name,
                sentNum,
                next(mentionID),
                ngdata,
            )
            subtrees = tree.findall(
                './/node[@begin="'
                + str(new_mention.begin)
                + '"][@end="'
                + str(new_mention.end)
                + '"]'
            )
            firstChild = subtrees[0].find('.//node[@word]')
            if (
                (
                    'pron' in firstChild.attrib
                    and firstChild.attrib['pron'] == 'true'
                )
                or (
                    'buiging' in firstChild.attrib
                    and firstChild.attrib['buiging'] == 'zonder'
                )
                or (
                    'pos' in firstChild.attrib
                    and firstChild.attrib['pos'] == 'num'
                )
                or ('index' in firstChild.attrib)
                or ('sc' in firstChild.attrib)
            ):
                pass
            elif ',' in new_mention.tokenList:
                handleComma(
                        new_mention, tree, sentNum, ngdata,
                        mention_list, mentionID)
            elif allWordsHaveAlpha(new_mention.tokenList):
                add_mention(mention_list, new_mention)


# 11.04/42.33/17.51
def findMWU(tree, sentNum, ngdata, mention_list, mentionID):
    mwu_rels = ['obj1', 'su', 'cnj', 'hd']  # hd 14/65
    for mention_node in tree.findall(".//node[@cat='mwu']"):
        len_ment = int(mention_node.attrib['end']) - int(
            mention_node.attrib['begin']
        )
        if mention_node.attrib['rel'] in mwu_rels:
            name = 'mwu_' + mention_node.attrib['rel']
            new_mention = make_mention(
                mention_node.attrib['begin'],
                mention_node.attrib['end'],
                tree,
                name,
                sentNum,
                next(mentionID),
                ngdata,
            )
            add_mention(mention_list, new_mention)


# 04.32/65.85/08.11
def findMWU2(tree, sentNum, ngdata, mention_list, mentionID):
    mwu_rels = ['obj1', 'su', 'cnj', 'hd']  # hd 14/65
    for mention_node in tree.findall(".//node[@cat='mwu']"):
        len_ment = int(mention_node.attrib['end']) - int(
            mention_node.attrib['begin']
        )
        if mention_node.attrib['rel'] in mwu_rels:
            prevDet = tree.find(
                ".//node[@pos='det'][@end='"
                + mention_node.attrib['begin']
                + "']"
            )
            if prevDet is not None:
                name = 'mwu_' + mention_node.attrib['rel']
                new_mention = make_mention(
                    int(mention_node.attrib['begin']) - 1,
                    mention_node.attrib['end'],
                    tree,
                    name,
                    sentNum,
                    next(mentionID),
                    ngdata,
                )
                add_mention(mention_list, new_mention)


# 14.56/65.00/23.79
def findSubj(tree, sentNum, ngdata, mention_list, mentionID):
    for mention_node in tree.findall(".//node[@rel='su']"):
        if 'cat' not in mention_node.attrib:
            new_mention = make_mention(
                mention_node.attrib['begin'],
                mention_node.attrib['end'],
                tree,
                'su',
                sentNum,
                next(mentionID),
                ngdata,
            )
            add_mention(mention_list, new_mention)


# 04.00/54.35/07.45
def findObj(tree, sentNum, ngdata, mention_list, mentionID):
    for mention_node in tree.findall(
        ".//node[@word][@ntype='soort'][@rel='obj1']"
    ):
        new_mention = make_mention(
            mention_node.attrib['begin'],
            mention_node.attrib['end'],
            tree,
            'noun',
            sentNum,
            next(mentionID),
            ngdata,
        )
        add_mention(mention_list, new_mention)


# 07.84/51.58/13.61
def findPron(tree, sentNum, ngdata, mention_list, mentionID):
    for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(
        ".//node[@frame='determiner(pron)']"
    ):
        new_mention = make_mention(
            mention_node.attrib['begin'],
            mention_node.attrib['end'],
            tree,
            'Pronoun',
            sentNum,
            next(mentionID),
            ngdata,
        )
        add_mention(mention_list, new_mention)


# 28.16/59.46/38.22
def findName(tree, sentNum, ngdata, mention_list, mentionID):
    for new_mention in stitch_names(
            tree.findall(".//node[@pos='name']"),
            tree, sentNum, mentionID, ngdata):
        add_mention(mention_list, new_mention)


# 00.80/50.00/01.57
def findNP2(tree, sentNum, ngdata, mention_list, mentionID):
    np_rels = ['obj1', 'su', 'app', 'cnj', 'body', 'sat', 'predc']
    for mention_node in tree.findall(".//node[@cat='np']"):
        len_ment = int(mention_node.attrib['end']) - int(
            mention_node.attrib['begin']
        )
        if (
            mention_node.attrib['rel'] in np_rels and len_ment > 4
        ):  # and len_ment < 10:
            for die in tree.findall(
                ".//node[@word='die']"
            ):  # @word='die' werkt beter
                if int(die.attrib['begin']) > int(
                    mention_node.attrib['begin']
                ) and int(die.attrib['end']) < int(mention_node.attrib['end']):
                    new_mention = make_mention(
                        mention_node.attrib['begin'],
                        die.attrib['begin'],
                        tree,
                        'die_np',
                        sentNum,
                        next(mentionID),
                        ngdata,
                    )
                    if allWordsHaveAlpha(new_mention.tokenList):
                        add_mention(mention_list, new_mention)


# Mention detection sieve, selects all NPs, pronouns, names
def mentionDetection(conll_list, tree_list, verbosity, sentenceDict, ngdata,
        mention_list):
    mention_id_list = []
    mention_dict = {}
    sentNum = 1
    mentionID = count()
    for tree in tree_list:
        mention_list = []
        sentenceDict[sentNum] = tree.find('sentence').text
        sentenceList = tree.find('sentence').text.split(' ')

        findNP(tree, sentNum, ngdata, mention_list, mentionID)
        # findMWU(tree, sentNum, ngdata, mention_list, mentionID)
        findMWU2(tree, sentNum, ngdata, mention_list, mentionID)
        findSubj(tree, sentNum, ngdata, mention_list, mentionID)
        findObj(tree, sentNum, ngdata, mention_list, mentionID)
        findPron(tree, sentNum, ngdata, mention_list, mentionID)
        findName(tree, sentNum, ngdata, mention_list, mentionID)
        findNP2(tree, sentNum, ngdata, mention_list, mentionID)

        if len(tree.findall('.//node')) > 2:
            for mention in mention_list:
                mention_id_list.append(mention.ID)
                mention_dict[mention.ID] = mention
        sentNum += 1

        # Sort list properly
    mention_id_list = sort_mentions(mention_id_list, mention_dict)
    if verbosity == 'high':
        print('found %d unique mentions' % (len(mention_id_list)))
    return mention_id_list, mention_dict
