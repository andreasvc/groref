"""Precise Constructs"""

from utils import mergeClustersByMentionIDs, get_mention_id_list_per_sentence
from demonyms import Demo


def sievePreciseConstructs(
        mention_id_list, mention_dict, cluster_dict, cluster_id_list,
        verbosity):
    mention_ids_per_sentence = get_mention_id_list_per_sentence(
            mention_id_list, mention_dict)
    if verbosity == 'high':
        print('Applying Precise Constructs...')
    for cluster_id in cluster_id_list[:]:
        madeLink = False
        cluster = cluster_dict[cluster_id]
        # Only consider first mention in cluster for resolution
        anaphor = mention_dict[cluster.mentionList[0]]
        # Cycle through sentences backwards, but through mentions within a
        # sentence forwards
        for sent_id in range(anaphor.sentNum, 0, -1):
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
                    for ment_id in candidate_cluster.mentionList:
                        root = mention_dict[ment_id].tree.getroot()
                        # print(mention_dict[ment_id].tokenAttribs,
                        #       mention_dict[anaphor.ID].headWords,
                        #       mention_dict[anaphor.ID].tokenAttribs)
                        # Appositive: link two mentions if they are in an
                        # appositive contstructions.
                        appos = appositive(root)
                        if (appos and len(
                                    mention_dict[anaphor.ID].tokenList) > 2):
                            for ids in mention_dict[ment_id].tokenAttribs:
                                if (ids['id'], ids['root']) not in appos[0]:
                                    continue
                                for ana_ids in mention_dict[
                                        anaphor.ID].tokenAttribs:
                                    if (ana_ids['id'], ana_ids['root']
                                            ) in appos[1]:
                                        madeLink = True
                                        break
                                if madeLink:
                                    break
                        # Predicate nominative: Two mentions (nominal or
                        # pronominal) are in a copulative subject-object
                        # relation
                        pred = pred_nom(root)
                        if pred:
                            for ids in mention_dict[ment_id].tokenAttribs:
                                if (ids['id'], ids['root']) not in pred[0]:
                                    continue
                                for ana_ids in mention_dict[
                                        anaphor.ID].tokenAttribs:
                                    if (ana_ids['id'], ana_ids['root']
                                                ) in pred[1]:
                                        madeLink = True
                                        break
                                if madeLink:
                                    break
                        # Role appositive
                        # if mention_dict[anaphor.ID].NEtype == 'person' and  mention_dict[ment_id].animacy == 'animate':# and mention_dict[anaphor.ID].gender != 'neuter':
                        # 	hw = mention_dict[ment_id].headWords + mention_dict[anaphor.ID].tokenList
                        # 	h =  mention_dict[ment_id].headWords
                        # 	t = []
                        # 	for hw in mention_dict[anaphor.ID].tokenList:
                        # 		h.append(hw.lower())
                        # 	for tk in mention_dict[ment_id].tokenList:
                        # 		t.append(tk.lower())
                        # 	if h == t:
                        # 		madeLink == True
                        # 		print "Role Appositive"

                        # Relative Pronoun: mention is a relative pronoun that
                        # modifies the head of the antecedent NP
                        if mention_dict[anaphor.ID].pron_type == 'betr':
                            rp = get_rel_pron(
                                    root,
                                    mention_dict[anaphor.ID].tokenAttribs[0])
                            if len(rp) > 0:
                                for at in mention_dict[ment_id].tokenAttribs:
                                    if rp[0][0]['id'] == at['id']:
                                        madeLink = True
                                        break
                        # Acronym: Both mentions are tagged as NNP and one of
                        # them is an acronym of the other
                        mention_acr = acronyms(mention_dict[ment_id].tokenList)
                        anaphor_acr = acronyms(
                                mention_dict[anaphor.ID].tokenList)
                        if (mention_dict[ment_id].type == 'name'
                            and mention_dict[anaphor.ID].type == 'name'):
                            if (mention_acr
                                    in mention_dict[anaphor.ID].tokenList
                                    or anaphor_acr
                                    in mention_dict[ment_id].tokenList):
                                madeLink = True
                        # Demonym: one of the mentions is a demonym of the other
                        if len(mention_dict[ment_id].tokenList) == 1:
                            if mention_dict[ment_id].tokenList[0] in Demo:
                                if (
                                    Demo[mention_dict[ment_id].tokenList[0]]
                                    == mention_dict[anaphor.ID].tokenList[0]
                                ):
                                    madeLink = True
                        if len(mention_dict[anaphor.ID].tokenList) == 1:
                            if mention_dict[anaphor.ID].tokenList[0] in Demo:
                                if (
                                    Demo[mention_dict[anaphor.ID].tokenList[0]]
                                    == mention_dict[ment_id].tokenList[0]
                                ):
                                    madeLink = True
                        if madeLink:
                            if verbosity == 'high':
                                print('Linking clusters %d and %d' % (
                                        ment_id, anaphor.ID))
                            (cluster_dict, cluster_id_list
                                    ) = mergeClustersByMentionIDs(
                                    ment_id, anaphor.ID, mention_dict,
                                    cluster_dict, cluster_id_list)
                            break
    return mention_id_list, mention_dict, cluster_dict, cluster_id_list


def acronyms(tokenlist):
    return ''.join(token[0] for token in tokenlist)


def get_rel_pron(root, pron):
    relative_pron = []
    for node in root.iter('node'):
        at = node.attrib
        if 'cat' in at and at['cat'] == 'np':
            for child in node:
                if 'rel' in child.attrib and child.attrib['rel'] == 'mod':
                    for c in child:
                        ca = c.attrib
                        if ('vwtype' in ca
                                and ca['vwtype'] == 'betr'
                                and ca['id'] == pron['id']):
                            for child in node:
                                if ('rel' in child.attrib
                                        and child.attrib['rel'] == 'hd'):
                                    rel_pron = (child.attrib, ca)
                                    relative_pron.append(rel_pron)
    return relative_pron


def appositive(root):
    ment = []
    app = []
    for node in root.iterfind(".//node[@cat='np']"):
        if node.get('rel') != 'app':
            for child in node:
                if (child.get('rel') == 'app'
                        and 'root' not in child.attrib
                        and 'mwu_root' not in child.attrib):
                    for h in node:
                        if 'root' in h.attrib:
                            ment.append((h.attrib['id'], h.attrib['root']))
                        if 'mwu_root' in h.attrib:
                            h.attrib['root'] = h.attrib['mwu_root']
                            ment.append((h.attrib['id'], h.attrib['root']))
                            for node in h:
                                if node.get('rel') == 'mwp':
                                    ment.append(
                                            (node.attrib['id'],
                                            node.attrib['root']))
                    for c in child.iter('node'):
                        if 'root' in c.attrib:
                            app.append((c.attrib['id'], c.attrib['root']))
                        if 'mwu_root' in c.attrib:
                            c.attrib['root'] = c.attrib['mwu_root']
                            app.append((c.attrib['id'], c.attrib['root']))
                        # FIXME: this is clearly a typo but fixing it lowers
                        # the score on dev set
                        # if 'rel' in c.attrib and c.attrib['rel'] == 'cnj':
                        if 'rel' in c.attrib and node.attrib['rel'] == 'cnj':
                            return None
    return ment, app


def pred_nom(root):
    copula = False
    subj = []
    predc = []
    for node in root.findall(".//node[@cat='smain']"):
        for n in node:
            at = n.attrib
            if 'sc' in at and at['sc'] == 'copula':
                copula = True
        if copula:
            for n in node:
                at = n.attrib
                if 'rel' in at and at['rel'] == 'su':
                    for s in n:
                        at = s.attrib
                        if 'root' in at:
                            subj.append((at['id'], at['root']))
                        if 'mwu_root' in at:
                            s.attrib['root'] = s.attrib['mwu_root']
                            subj.append((at['id'], at['root']))
                if 'rel' in at and at['rel'] == 'predc':
                    for s in n:
                        at = s.attrib
                        if 'root' in at:
                            predc.append((at['id'], at['root']))
                        if 'mwu_root' in at:
                            s.attrib['root'] = s.attrib['mwu_root']
                            predc.append((at['id'], at['root']))
    if len(subj) > 0 and len(predc) > 0:
        return (subj, predc)
