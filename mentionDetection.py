#!/usr/bin/env python
# -*- coding: utf8 -*-

'''Mention detection sieve of the coreference resolution system'''

from utils import *
mention_list = []

# 28.16/48.75/35.70
def findNP(tree, sentNum):
	global mention_list
	np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
	for mention_node in tree.findall(".//node[@cat='np']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in np_rels and len_ment < 7: 
			name = 'np_' + mention_node.attrib['rel']
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum)
			add_mention(mention_list, new_mention)
# 08.64/69.23/15.36 
def findMWU(tree, sentNum):
	global mention_list
	mwu_rels = ['obj1','su','cnj'] #hd 14/65 
	for mention_node in tree.findall(".//node[@cat='mwu']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
			name = 'mwu_' + mention_node.attrib['rel']
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum)
			add_mention(mention_list, new_mention)

# 14.72/65.71/24.05
def findSubj(tree, sentNum):
	global mention_list
	for mention_node in tree.findall(".//node"): #TODO, refactor
		if 'cat' not in mention_node.attrib and mention_node.attrib['rel'] == 'su':
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'su', sentNum)
			add_mention(mention_list, new_mention)	

# 04.32/56.25/08.02
def findObj(tree, sentNum):
	global mention_list
	for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
		new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'noun', sentNum)
		add_mention(mention_list, new_mention)

# 07.84/52.13/13.63
def findPron(tree, sentNum):
	global mention_list
	for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
		new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Pronoun', sentNum)
		add_mention(mention_list, new_mention)

# 25.44/60.23/35.77
def findName(tree, sentNum):
	global mention_list
	for new_mention in stitch_names(tree.findall(".//node[@pos='name']"), tree, sentNum):
		add_mention(mention_list, new_mention)

# 02.08/10.74/03.49
def findNP2(tree, sentNum):
	global mention_list
	np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
	for mention_node in tree.findall(".//node[@cat='np']"):
		len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
		if mention_node.attrib['rel'] in np_rels and len_ment > 4:	
			rem_cand = tree.find(".//node[@end='" + mention_node.attrib['end'] + "'][@rel='mod']") 
			if rem_cand != None and int(rem_cand.attrib['begin']) > int(mention_node.attrib['begin']):
				name = 'broken_np' + mention_node.attrib['rel']
				new_mention = make_mention(mention_node.attrib['begin'], rem_cand.attrib['begin'], tree, name, sentNum)
				add_mention(mention_list, new_mention)
		
			rem_cand2 = tree.find(".//node[@end='" + mention_node.attrib['end'] + "'][@cat='pp']")
			if rem_cand2 != None and int(rem_cand2.attrib['begin']) > int(mention_node.attrib['begin']):
				name = 'broken_np' + mention_node.attrib['rel']
				new_mention = make_mention(mention_node.attrib['begin'], rem_cand2.attrib['begin'], tree, name, sentNum)
				add_mention(mention_list, new_mention)

# Mention detection sieve, selects all NPs, pronouns, names		
def mentionDetection(conll_list, tree_list, docFilename, verbosity, sentenceDict):
	global mention_list

	mention_id_list = []
	mention_dict = {}
	for tree in tree_list:
		mention_list = []
		sentNum = tree.find('comments').find('comment').text
		sentNum = int(re.findall('#[0-9]+', sentNum)[0][1:])
		sentenceDict[int(sentNum)] = tree.find('sentence').text
		
		findNP(tree, sentNum)
		findMWU(tree, sentNum)
		findSubj(tree, sentNum)
		findObj(tree, sentNum)
		findPron(tree, sentNum)
		findName(tree, sentNum)
		#findNP2(tree, sentNum)
		
		if len(tree.findall('.//node')) > 2: 
			for mention in mention_list:
				mention_id_list.append(mention.ID)
				mention_dict[mention.ID] = mention
	for mention in mention_list:
		print mention.begin, mention.end, mention.ID
	print mention_id_list
	# Sort list properly
	mention_id_list = sort_mentions(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'found %d unique mentions' % (len(mention_id_list))
	return mention_id_list, mention_dict


