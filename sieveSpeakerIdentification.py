#!/usr/bin/env python

from utils import *

'''This sieve matches speakers to compatible pronouns,
using shallow discourse understanding to handle quotations and conversation
transcripts. 

We begin by identifying speakers within text. In non-conversational text, we use a simple heuristic that searches
for the subjects of reporting verbs (e.g., say) in the same sentence or neighboring
sentences to a quotation. In conversational text, speaker information is provided in the
data set.'''

replist = ['begin', 'onthul', 'loof', 'kondig_aan', 'beweer', 'breng_in', 'deel_mee', 'merk_op', 'zeg_op', 'spreek', 'breng_uit', 'druk_uit', 'uit', 'spreek_uit', 'verklaar', 'verkondig', 'vermeld', 'vertel', 'verwoord', 'duid_aan', 'benoem', 'tendeer_in', 'meen', 'noem', 'oordeel', 'stel', 'vind', 'beduid', 'behels', 'beteken', 'bewijs', 'beveel', 'gebied', 'draag_op', 'neem_aan', 'veronderstel', 'merk_aan', 'verwijt', 'beloof', 'zeg_toe', 'schrijf_voor', 'geef_aan', 'stip_aan', 'kondig_af', 'maak_bekend', 'bericht', 'beschrijf', 'declareer', 'gewaag', 'meld', 'geef_op', 'neem_op', 'teken_op', 'relateer', 'proclameer', 'publiceer', 'rapporteer', 'leg_vast', 'vernoem', 'versla', 'zeg', 'betoon', 'betuig', 'manifesteer', 'openbaar', 'peer_op', 'slaak', 'spui', 'sla_uit', 'stort_uit', 'stoot_uit', 'vertolk', 'ventileer', 'deponeer', 'expliciteer', 'getuig', 'ontvouw', 'pretendeer', 'doe_uiteen', 'zet_uiteen', 'verzeker', 'kleed_in', 'lucht', 'breng_over', 'toon', 'vervat', 'geef_weer', 'betoog', 'claim', 'suggereer', 'houd_vol', 'geef_voor', 'wend_voor', 'verdedig', 'spreek_aan', 'bestempel', 'betitel', 'kwalificeer', 'som_op', 'draai_af', 'debiteer', 'deel_mede', 'dis_op', 'kraam_uit', 'verhaal', 'poneer', 'postuleer', 'leg_voor', 'fluister']

def find_sub(root):
	sublist = []
	for node in root.iter('node'):		
		at = node.attrib
		for n in node.findall('node'):
			c = n.attrib
			if 'root' in c and c['root'] in replist:	
				for n in node.findall('node'):
					ns = n.attrib
					if 'rel' in ns and ns['rel'] == 'su':
						if n not in sublist:
							sublist.append(n)
	return sublist
	
def quote_range(root):
	rang = []
	for node in root.iter('sentence'):
		lensent = len(node.text.split(' '))	
		quotelist = ['&apos;&apos;', '"', "'", '``', "''"]
		text = node.text.replace('``', '`` ').replace("' '", "''").replace('&apos; &apos;', "&apos;&apos;").encode('UTF8')
		sent = text.split(' ')
		rg = []	
		for item in range(len(sent)):
			if sent[item] in quotelist:
				rg.append(item)
		lst = rang_recursive(rg, [])
		if lst != None:
			for item in lst:
				rang.append(item)
	return rang

def rang_recursive(rang, lst):
	if len(rang) % 2 == 0:
		outer = (rang[0], rang[-1])
		lst.append(outer)
		del(rang[0])
		del(rang[-1])
		if len(rang) > 0:
			return rang_recursive(rang, lst)
		else:
			return lst
					
def sieveSpeakerIdentification(mention_id_list, mention_dict, cluster_dict, cluster_id_list, verbosity):
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'Speaker identification...'
	for cluster_id in cluster_id_list[:]:
		madeLink = False
		'''Initialize linking constraints here'''
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolutio
		'''Check for constraints on the anaphor here'''
		for sent_id in range(anaphor.sentNum, 0, -1): # Cycle through sentences backwards, but through mentions within a sentence forwards
			if madeLink:
				break
			if sent_id in mention_ids_per_sentence: # Not empty
				for candidate_mention_id in mention_ids_per_sentence[sent_id]:
					if madeLink:
						break
					if candidate_mention_id == anaphor.ID: # Don't look ahead of anaphor
						break
					candidate_cluster = cluster_dict[mention_dict[candidate_mention_id].clusterID]
					''' search for subjects of reporting verbs'''
					for ment_id in candidate_cluster.mentionList:
						root = mention_dict[ment_id].tree.getroot()
						anaphor_root = mention_dict[anaphor.ID].tree.getroot()
						su_list = ['su', 'mwu_su', 'np_su']	
						I = ['ik', 'mij', 'me', 'mijn']
						We = ['wij', 'ons', 'onze']
						You = ['jij', 'je', 'jullie', 'U']					
						Subject = False
						Quote = False
						for node in anaphor_root.iter('node'):
							at = node.attrib
							if 'frame' in at:
								if at['frame'] == 'punct(aanhaal_both)':
									Quote = True
						if mention_dict[ment_id].type in su_list:
							Subject = True							
						if Subject and Quote:							
							anaphorlist = []
							quote =	quote_range(anaphor_root)
							sub_verb = find_sub(root)
							for subj in mention_dict[ment_id].tokenAttribs:
								for su in sub_verb:
									if subj['id'] == su.attrib['id']:
										q_list = []
										for q in quote:
											if mention_dict[ment_id].begin not in range(q[0], q[1]):
												q_list.append(q)
										for q in q_list:
											for node in anaphor_root.iter('node'):
												at = node.attrib
												if int(at['begin']) in range(q[0], q[1]) and 'pos' in at and at['pos'] == 'pron':
														anaphorlist.append(at)
							for attrib in anaphor.tokenAttribs:
								for pron in anaphorlist:
									if attrib['id'] == pron['id']:
										if attrib['root'] in I:
											madeLink = True
										elif attrib['root'] in You:
											madeLink = True						
						'''Check things against other mentions in the candidate cluster here, if necessary'''
						if madeLink:
							if verbosity == 'high':
								print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(ment_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)	
							break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
