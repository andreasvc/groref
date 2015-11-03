#!/usr/bin/env python

from utils import *
from demonyms import Demo

def Acronyms(tokenlist):
	ac = []
	for token in tokenlist:
		ac.append(token[0])
	return ''.join(ac)

'''Precise Constructs'''
def sievePreciseConstructs(mention_id_list, mention_dict, cluster_dict, cluster_id_list, verbosity):
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	if verbosity == 'high':
		print 'Applying Precise Constructs...'
	for cluster_id in cluster_id_list[:]:
		ExactEntityMatch = False
		RelaxedEntityMatch = False
		madeLink = False
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution				
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
					for ment_id in candidate_cluster.mentionList:
						'''Appositive'''
						#link two mentions if they are in an appositive contstructions
						#third children of a parent NP whose expansion begins with (NP, NP) when there is not a conjunction in the expansion
						
						'''Predicate nominative'''
						#Two mentions (nominal or pronominal) are in a copulative subject-object relation
						
						'''Relative Pronoun'''
						#mention is a relative pronoun that modifies the head of the antecedent NP
						#print mention_dict[anaphor.ID].type, mention_dict[anaphor.ID].headWords
						if  mention_dict[anaphor.ID].pron_type == 'betr':
							madeLink = True
							#print mention_dict[ment_id].tokenAttribs, mention_dict[anaphor.ID].headWords, mention_dict[anaphor.ID].tokenAttribs
						'''Acronym'''
						#Both mentions are tagged as NNP and one of them is an acronym of the other
						mention_acr = Acronyms(mention_dict[ment_id].tokenList) 
						anaphor_acr = Acronyms(mention_dict[anaphor.ID].tokenList)
						if mention_dict[ment_id].type == 'name' and mention_dict[anaphor.ID].type =='name':						
							if mention_acr in mention_dict[anaphor.ID].tokenList or anaphor_acr in mention_dict[ment_id].tokenList:
								madeLink = True					
						'''Demonym'''
						#One of the mentions is a demonym of the other
						if len(mention_dict[ment_id].tokenList) == 1:
							if mention_dict[ment_id].tokenList[0] in Demo:
								if Demo[mention_dict[ment_id].tokenList[0]] == mention_dict[anaphor.ID].tokenList[0]:
									madeLink = True
						if len(mention_dict[anaphor.ID].tokenList) == 1:
							if mention_dict[anaphor.ID].tokenList[0] in Demo:
								if Demo[mention_dict[anaphor.ID].tokenList[0]] == mention_dict[ment_id].tokenList[0]:
									madeLink = True						
						if madeLink:							
							if verbosity == 'high':						
								print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)							
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(ment_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)	
							madeLink = True					
						if madeLink:
							break
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list


