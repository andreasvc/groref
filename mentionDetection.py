#!/usr/bin/env python
# -*- coding: utf8 -*-

'''Mention detection sieve of the coreference resolution system'''

from utils import *



	
# Mention detection sieve, selects all NPs, pronouns, names		
def mentionDetection(conll_list, tree_list, docFilename, verbosity, sentenceDict):
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
				new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum)
				add_mention(mention_list, new_mention)
				
		
		mwu_rels = ['obj1','su','cnj'] #hd 14/65 
		for mention_node in tree.findall(".//node[@cat='mwu']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in mwu_rels:# and len_ment < 3: 
				name = 'mwu_' + mention_node.attrib['rel']
				new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, name, sentNum)
				add_mention(mention_list, new_mention)

		for mention_node in tree.findall(".//node"):
			if 'cat' not in mention_node.attrib and mention_node.attrib['rel'] == 'su':
				new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'su', sentNum)
				add_mention(mention_list, new_mention)
		
		for mention_node in tree.findall(".//node[@word][@ntype='soort'][@rel='obj1']"):
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'noun', sentNum)
			add_mention(mention_list, new_mention)
	
		for mention_node in tree.findall(".//node[@pdtype='pron']") + tree.findall(".//node[@frame='determiner(pron)']"):
			new_mention = make_mention(mention_node.attrib['begin'], mention_node.attrib['end'], tree, 'Pronoun', sentNum)
			add_mention(mention_list, new_mention)

		for new_mention in stitch_names(tree.findall(".//node[@pos='name']"), tree, sentNum):
			mention_list = add_mention(mention_list, new_mention)

		"""
		np_rels = ['obj1','su','app','cnj','body','sat','predc'] 
		for mention_node in tree.findall(".//node[@cat='np']"):
			len_ment = int(mention_node.attrib['end']) - int(mention_node.attrib['begin'])
			if mention_node.attrib['rel'] in np_rels and len_ment > 4:
				rem_cands = tree.findall(".//node[@end='" + mention_node.attrib['end'] + "'][@rel='mod']") + tree.findall(".//node[@end='" + mention_node.attrib['end'] + "'][@cat='pp']")
				
				for rem_cand in rem_cands:
					name = 'broken_np' + mention_node.attrib['rel']
					new_mention = make_mention(mention_node.attrib['begin'], rem_cand.attrib['begin'], tree, name, sentNum)
					add_mention(mention_list, new_mention)
					
					#mention = mention_list[len(mention_list)-1]
					#print mention.begin, mention.end
		"""
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
	# Sort list properly
	mention_id_list = sort_mentions(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'found %d unique mentions' % (len(mention_id_list))
	return mention_id_list, mention_dict	
