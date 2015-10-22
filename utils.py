#!/usr/bin/env python

import colorama as c

# Function that takes two mention ids, and merges the clusters they are part of, returns cluster list
def mergeClustersByMentionIDs(idx1, idx2, mention_dict, cluster_list):
	mention1 = mention_dict[idx1]
	mention2 = mention_dict[idx2]
	if mention1.clusterID == mention2.clusterID: # Cannot merge if mentions are part of same cluster
		return
	for idx, cluster in enumerate(cluster_list): # Find clusters by ID, could be more efficient
		if mention1.clusterID == cluster.ID:
			cluster1 = cluster
		if mention2.clusterID == cluster.ID:
			cluster2 = cluster
			cluster2_idx = idx
	# Put all mentions of cluster2 in cluster1
	for mentionID in cluster2.mentionList:
		cluster1.mentionList.append(mentionID)
		for mention_id, mention in mention_dict.iteritems():
			if mention.ID == mentionID:
				mention.clusterID = cluster1.ID
	del cluster_list[cluster2_idx]
	return cluster_list
	
# Returns coloured text
def colour_text(text, colour):
	if colour.lower() == 'red':
		return c.Fore.RED + text + c.Fore.RESET
	elif colour.lower() == 'blue':
		return c.Fore.BLUE + text + c.Fore.RESET	
	elif colour.lower() == 'green':
		return c.Fore.GREEN + text + c.Fore.RESET	
	elif colour.lower() == 'white':
		return c.Fore.WHITE + text + c.Fore.RESET
	elif colour.lower() == 'yellow':
		return c.Fore.YELLOW + text + c.Fore.RESET		
	elif colour.lower() == 'cyan':
		return c.Fore.CYAN + text + c.Fore.RESET
		
# Prints all mentions and attributes in order		
def print_all_mentions_ordered(mention_id_list, mention_dict):
	for mention_id in mention_id_list:
		print mention_dict[mention_id].__dict__
		
# Takes mention_id_list, returns a dict, with mention_ids per sentence
def get_mention_id_list_per_sentence(mention_id_list, mention_dict):
	mention_ids_per_sentence = {}
	for mention_id in mention_id_list:
		mention = mention_dict[mention_id]
		if mention.sentNum in mention_ids_per_sentence:
			mention_ids_per_sentence[mention.sentNum].append(mention.ID)
		else:
			mention_ids_per_sentence[mention.sentNum] = [mention.ID]
	return mention_ids_per_sentence
