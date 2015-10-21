import find_errors
import count_nodes


def clean_attribs(atr_dict):
    del attributes['begin']
    del attributes['end']
    del attributes['id']
    del attributes['sense']
    del attributes['word']
    del attributes['lemma']
    del attributes['root']


print(len(find_errors.get_errors([1,2,3])))



