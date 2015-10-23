#!/usr/bin/env python

from utils import *

'''Strictest head-matching sieve'''
def sieveHeadMatch1(mention_id_list, mention_dict, cluster_dict, cluster_id_list):

	print_all_mentions_ordered(mention_id_list, mention_dict)
	mention_ids_per_sentence = get_mention_id_list_per_sentence(mention_id_list, mention_dict)
	print mention_ids_per_sentence
	for cluster_id in cluster_id_list:
		cluster = cluster_dict[cluster_id]
		print cluster.__dict__
	print 'Doing head-matching...'
	for cluster_id in cluster_id_list[:]:
		print 'looking at cluster: %d' % cluster_id
		entityHeadMatch = False
		wordInclusion = False
		compModsOnly = False
		NotIWithinI = True
		madeLink = False # IF a link is made, go to the next cluster
		if madeLink:
			continue
		cluster = cluster_dict[cluster_id]
		anaphor = mention_dict[cluster.mentionList[0]] # Only consider first mention in cluster for resolution
		# Set up correct cycling through candidate anaphora and antecedents
		if not anaphor.headWords: # If no headwords, look at next candidate
			continue
		for sent_id in range(anaphor.sentNum, 0, -1): # Cycle through sentences backwards, but through mentions within a sentence forwards
			if madeLink:
				break
			if sent_id in mention_ids_per_sentence: # Not empty
				for candidate_mention_id in mention_ids_per_sentence[sent_id]:
					if madeLink:
						break
					if candidate_mention_id == anaphor.ID: # Don't look ahead of anaphor
						break
#					print_all_mentions_ordered(mention_id_list, mention_dict)
					candidate_cluster = cluster_dict[mention_dict[candidate_mention_id].clusterID]
					for ment_id in candidate_cluster.mentionList: # Assume only 1 headword
						# Check constraints here
#						print anaphor.headWords
#						print mention_dict[ment_id].headWords
						if set(anaphor.headWords).issubset(set(mention_dict[ment_id].headWords)):
							entityHeadMatch = True # All headwords of anaphor in headwords of a mention in a cluster
							print 'Linking clusters %d and %d' % (ment_id, anaphor.ID)
#							print ment_id
#							print anaphor.ID
						if entityHeadMatch:
							cluster_dict, cluster_id_list = mergeClustersByMentionIDs(ment_id, anaphor.ID, \
								mention_dict, cluster_dict, cluster_id_list)
#							print cluster_id_list
							madeLink = True
						if madeLink:
							break
	for cluster_id in cluster_id_list:
		print cluster_dict[cluster_id].__dict__
	return mention_id_list, mention_dict, cluster_dict, cluster_id_list
