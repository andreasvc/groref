#!/usr/bin/env python
# -*- coding: utf8 -*-

'''Mention detection sieve of the coreference resolution system'''

from utils import *
mention_list = []

# 28.16/48.75/35.70
def findNP(tree, sentNum, ngdata):
	global mention_list
	np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
	for mention_node in tree.findall(".//node[@cat='np']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in np_rels and len_ment < 7: 
			name = 'np_' + mention_node.attrib['rel']
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum, ngdata)
			if ',' in new_mention.tokenList:
				if new_mention.tokenList[1] == ',' and len(new_mention.tokenList) > 3:
					add_mention(mention_list, new_mention)
				#TODO, edit for mw locations, and rm from findName 
				elif (len(new_mention.tokenList) == 3 and 
						new_mention.tokenList[1] == ',' and
					'neclass' in new_mention.tokenAttribs[0] and
					new_mention.tokenAttribs[0]['neclass'] == 'LOC'):
					add_mention(mention_list, new_mention)
					new_mention1 = make_mention(new_mention.tokenList.index(',') + new_mention.begin + 1, new_mention.end, tree, 'np_comma', sentNum, ngdata)
					add_mention(mention_list, new_mention)
				else:
					new_mention1 = make_mention(new_mention.begin, new_mention.begin + new_mention.tokenList.index(','), tree, 'np_comma', sentNum, ngdata)
					new_mention2 = make_mention(new_mention.tokenList.index(',') + new_mention.begin + 1, new_mention.end, tree, 'np_comma', sentNum, ngdata)
					add_mention(mention_list, new_mention1)
					add_mention(mention_list, new_mention2)
			else:
				add_mention(mention_list, new_mention)


# 08.64/69.23/15.36 
def findMWU(tree, sentNum, ngdata):
	global mention_list
	mwu_rels = ['obj1','su','cnj', 'hd'] #hd 14/65 
	for mention_node in tree.findall(".//node[@cat='mwu']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
			name = 'mwu_' + mention_node.attrib['rel']
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum, ngdata)
			add_mention(mention_list, new_mention)

def findMWU2(tree, sentNum, ngdata):
	global mention_list
	mwu_rels = ['obj1','su','cnj', 'hd'] #hd 14/65 
	for mention_node in tree.findall(".//node[@cat='mwu']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
			prevDet = tree.find(".//node[@pos='det'][@end='" + mention_node.attrib['begin'] + "']")
			if prevDet != None:
				name = 'mwu_' + mention_node.attrib['rel']
				new_mention = make_mention(int(mention_node.attrib['begin']) - 1, mention_node.attrib['end'], tree, name, sentNum, ngdata)
				add_mention(mention_list, new_mention)

# 14.72/65.71/24.05
def findSubj(tree, sentNum, ngdata):
	global mention_list
	for mention_node in tree.findall(".//node[@rel='su']"):
		if 'cat' not in mention_node.attrib:
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'su', sentNum, ngdata)
			add_mention(mention_list, new_mention)	

# 04.32/56.25/08.02
def findObj(tree, sentNum, ngdata):
	global mention_list
	for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
		new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'noun', sentNum, ngdata)
		add_mention(mention_list, new_mention)

# 07.84/52.13/13.63
def findPron(tree, sentNum, ngdata):
	global mention_list
	for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
		new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Pronoun', sentNum, ngdata)
		add_mention(mention_list, new_mention)

# 25.44/60.23/35.77
def findName(tree, sentNum, ngdata):
	global mention_list
	for new_mention in stitch_names(tree.findall(".//node[@pos='name']"), tree, sentNum, ngdata):
		add_mention(mention_list, new_mention)

# 02.08/10.74/03.49
def findNP2(tree, sentNum, ngdata):
	global mention_list
	np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
	for mention_node in tree.findall(".//node[@cat='np']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in np_rels and len_ment > 4:	
			rem_cand = tree.find(".//node[@end='" + mention_node.attrib['end'] + "'][@rel='mod']") 
			if rem_cand != None and int(rem_cand.attrib['begin']) > int(mention_node.attrib['begin']):
				name = 'broken_np' + mention_node.attrib['rel']
				new_mention = make_mention(mention_node.attrib['begin'], rem_cand.attrib['begin'], tree, name, sentNum, ngdata)
				add_mention(mention_list, new_mention)
		
			rem_cand2 = tree.find(".//node[@end='" + mention_node.attrib['end'] + "'][@cat='pp']")
			if rem_cand2 != None and int(rem_cand2.attrib['begin']) > int(mention_node.attrib['begin']):
				name = 'broken_np' + mention_node.attrib['rel']
				new_mention = make_mention(mention_node.attrib['begin'], rem_cand2.attrib['begin'], tree, name, sentNum, ngdata)
				add_mention(mention_list, new_mention)

def findNP3(word_list, sentNum, ngdata):
	global mention_list
	# vind alle opeenvolgende woorden met een hoofdletter
	# voeg lidwoord ervoor toe

	
# Mention detection sieve, selects all NPs, pronouns, names		
def mentionDetection(conll_list, tree_list, docFilename, verbosity, sentenceDict, ngdata):
	global mention_list

	mention_id_list = []
	mention_dict = {}
	for tree in tree_list:
		mention_list = []
		sentNum = tree.find('comments').find('comment').text
		sentNum = int(re.findall('#[0-9]+', sentNum)[0][1:])
		sentenceDict[int(sentNum)] = tree.find('sentence').text
		sentenceList = tree.find('sentence').text.split(' ')
		print sentenceList
		
		findNP(tree, sentNum, ngdata)
		#findMWU(tree, sentNum, ngdata)
		findMWU2(tree, sentNum, ngdata)
		findSubj(tree, sentNum, ngdata)
		findObj(tree, sentNum, ngdata)
		findPron(tree, sentNum, ngdata)
		findName(tree, sentNum, ngdata)
		#findNP2(tree, sentNum, ngdata)
		findNP3(sentenceList, sentNum, ngdata)
		
		if len(tree.findall('.//node')) > 2: 
			for mention in mention_list:
				mention_id_list.append(mention.ID)
				mention_dict[mention.ID] = mention
				
	# Sort list properly
	mention_id_list = sort_mentions(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'found %d unique mentions' % (len(mention_id_list))
	return mention_id_list, mention_dict


