#!/usr/bin/env python
# -*- coding: utf8 -*-

'''Mention detection sieve of the coreference resolution system'''

from utils import *

# Helper for mentionDetection()
def make_mention(begin, end, tree, mention_type, sentNum):
	global mentionID
	new_ment = Mention(mentionID)
	mentionID += 1
	new_ment.type = mention_type
	new_ment.begin = int(begin)
	new_ment.end = int(end)
	new_ment.numTokens = new_ment.end - new_ment.begin
	new_ment.sentNum = sentNum
	for node in tree.findall(".//node[@word]"):
		if int(node.attrib['begin']) >= int(begin) and int(node.attrib['end']) <= int(end):
			new_ment.tokenList.append(node.attrib["word"])
			new_ment.tokenAttribs.append(node.attrib)
	if mention_type.lower()[:2] == 'np':
		mention_node = tree.find(".//node[@cat='np'][@begin='" + begin + "'][@end='" + end + "']")
		head_node = mention_node.find("./node[@rel='hd']")
		new_ment.head_begin = int(head_node.attrib['begin']) - new_ment.begin
		new_ment.head_end = int(head_node.attrib['end']) - new_ment.begin
		new_ment.headWords = new_ment.tokenList[new_ment.head_begin:new_ment.head_end]
	if mention_type == 'Name': # Add last part of names as headword
		new_ment.head_begin = len(new_ment.tokenList) - 1
		new_ment.head_end = len(new_ment.tokenList)
		new_ment.headWords = new_ment.tokenList[-1:]
	if mention_type == 'noun':
		new_ment.head_begin = 0
		new_ment.head_end = 1
		new_ment.headWords = [new_ment.tokenList[0]]
	return new_ment
	
# Mention detection sieve, selects all NPs, pronouns, names		
def mentionDetection(conll_list, tree_list, docFilename, verbosity, sentenceDict):
#	global mentionID, sentenceDict
	mention_id_list = []
	mention_dict = {}
	for tree in tree_list:
		mention_list = []
		
		sentNum = tree.find('comments').find('comment').text
		sentNum = int(re.findall('#[0-9]+', sentNum)[0][1:])
		sentenceDict[int(sentNum)] = tree.find('sentence').text
		
		np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
		for mention_node in tree.findall(".//node[@cat='np']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in np_rels and len_ment < 7: 
				name = 'np_' + mention_node.attrib['rel']
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum))
		
		mwu_rels = ['obj1','su','cnj'] #hd 14/65 
		for mention_node in tree.findall(".//node[@cat='mwu']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
				name = 'mwu_' + mention_node.attrib['rel']
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum))

		for mention_node in tree.findall(".//node"):
			if 'cat' not in mention_node.attrib and mention_node.attrib['rel'] == 'su':
				mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'su', sentNum))
		
		for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'noun', sentNum))
	
		for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Pronoun', sentNum))

		# Take all name elements, some of which might be parts of same name. Those are stitched together later.
		for mention_node in tree.findall(".//node[@pos='name']"):
			mention_list.append(make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Name', sentNum))


		#TODO, look at children nodes, vooral bij relaties met lage precisie!
		
		"""	
		for mention_node in tree.findall(".//node[@cat='np']"):
			new_ment = make_mention(mention_node, 'NP', sentNum)
			new_ment.tokenList = []
			for node in mention_node.iter():
				if "word" in node.attrib:
					if 'pos' in node.attrib and node.attrib['pos'] == 'adv' and int(new_ment.begin) == int(node.attrib['begin']):
						#if np starts with adv, remove
						new_ment.begin = new_ment.begin + 1
						new_ment.numTokens = new_ment.numTokens - 1
					else: 
						new_ment.tokenList.append(node.attrib["word"])
			mention_list.append(new_ment)
		"""

		if len(tree.findall('.//node')) > 2: 
			for mention in mention_list:
				mention_id_list.append(mention.ID)
				mention_dict[mention.ID] = mention
		if verbosity == 'high':
			print 'Detecting mentions in sentence number %s' % (sentNum)
			print 'NP:   %d' % (len(tree.findall(".//node[@cat='np']")))
			print 'NP2:  %d' % (len(tree.findall(".//node[@lcat='np'][@ntype='soort']")))
			print 'DetN: %d' % (len(tree.findall(".//node[@pos='det']../node[@pos='noun']")))
			print 'MWU:  %d' % (len(tree.findall(".//node[@cat='mwu']")))
			print 'DU:   %d' % (len(tree.findall(".//node[@cat='du']")))
			print 'PRON: %d' % (len(tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']")))
	# Stitch together split name-type mentions
	mention_id_list, mention_dict = stitch_names(mention_id_list, mention_dict)
	#remove duplicates:
	bef_dup = len(mention_id_list)	
	mention_id_list, mention_dict = remove_duplicates(mention_id_list, mention_dict)
	# Sort list properly
	mention_id_list = sort_mentions(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'found %d unique mentions' % (len(mention_id_list))
		print 'and %d duplicates (which are removed)' % (bef_dup - len(mention_id_list))
	return mention_id_list, mention_dict	
