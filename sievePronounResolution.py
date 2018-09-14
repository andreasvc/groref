"""Pronoun resolution sieve"""

from utils import mergeClustersByMentionIDs, get_mention_id_list_per_sentence


def sievePronounResolution(mention_id_list, mention_dict, cluster_dict,
        cluster_id_list, verbosity):
    if verbosity == 'high':
        print('Doing pronoun resolution...')
    mention_ids_per_sentence = get_mention_id_list_per_sentence(
        mention_id_list, mention_dict)
    for cluster_id in cluster_id_list[:]:
        # Initialize linking constraints here
        matchNumber = False
        matchGender = False
        matchPerson = False
        # matchAnimacy = False
        matchNER = False
        madeLink = False
        if madeLink:
            continue
        cluster = cluster_dict[cluster_id]
        # Only consider first mention in cluster for resolution
        anaphor = mention_dict[cluster.mentionList[0]]
        # Check for constraints on the anaphor here
        if anaphor.type.lower() != 'pronoun':  # Skip non-pronouns
            continue
        if verbosity == 'high':
            print('Checking this anaphor:',
                    anaphor.tokenList, {
                    'type': anaphor.type,
                    'numb': anaphor.number,
                    'gend': anaphor.gender,
                    'anim': anaphor.animacy,
                    'pers': anaphor.person})

        # Cycle through sentences backwards, but through mentions within a
        # sentence forwards
        for sent_id in range(anaphor.sentNum, max(0, anaphor.sentNum - 3), -1):
            if madeLink:
                break
            if sent_id in mention_ids_per_sentence:  # Not empty
                for candidate_mention_id in mention_ids_per_sentence[sent_id]:
                    if madeLink:
                        break
                    # Don't look ahead of anaphor
                    if candidate_mention_id == anaphor.ID:
                        break
                    candidate_cluster = cluster_dict[
                            mention_dict[candidate_mention_id].clusterID]
                    if verbosity == 'high':
                        print('looking at cluster %d' % candidate_cluster.ID)
                    # Check things against the candidate mention here
                    for ment_id in candidate_cluster.mentionList:
                        # Check things against other mentions in the candidate
                        # cluster here, if necessary
                        matchNumber = False
                        matchGender = False
                        matchPerson = False
                        matchNER = False
                        cluster_mention = mention_dict[ment_id]
                        if verbosity == 'high':
                            print(cluster_mention.tokenList,
                                    {
                                        'type': cluster_mention.type,
                                        'numb': cluster_mention.number,
                                        'gend': cluster_mention.gender,
                                        'anim': cluster_mention.animacy,
                                        'netype': cluster_mention.NEtype})
                        if (cluster_mention.number == anaphor.number
                                or anaphor.number == 'unknown'):
                            matchNumber = True
                        if (cluster_mention.gender == anaphor.gender
                                or anaphor.gender == 'unknown'):
                            matchGender = True
                        if anaphor.animacy == 'animate':
                            if (cluster_mention.NEtype == 'person'
                                    or cluster_mention.NEtype == 'misc'):
                                matchNER = True
                            if (cluster_mention.NEtype == ''
                                    or cluster_mention.NEtype == 'unknown'):
                                matchNER = True
                        else:
                            if cluster_mention.NEtype != 'person':
                                matchNER = True
                            if (cluster_mention.NEtype == ''
                                    or cluster_mention.NEtype == 'unknown'):
                                matchNER = True
                        if cluster_mention.type.lower() == 'pronoun':
                            if (cluster_mention.person == anaphor.person
                                    or anaphor.person == 'unknown'):
                                matchPerson = True
                            if (matchNumber and matchGender
                                    and matchPerson and matchNER):
                                madeLink = True
                        else:
                            if matchNumber and matchGender and matchNER:
                                madeLink = True
                        if madeLink:
                            if verbosity == 'high':
                                print('Linking clusters %d and %d' % (
                                        ment_id, anaphor.ID))
                            (cluster_dict, cluster_id_list
                                    ) = mergeClustersByMentionIDs(
                                    candidate_mention_id, anaphor.ID,
                                    mention_dict, cluster_dict,
                                    cluster_id_list)
                            break
    return mention_id_list, mention_dict, cluster_dict, cluster_id_list
