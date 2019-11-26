import json
import optparse
from collections import Counter


def count_candidates_filtered_in(path='candidates_filtered_in.json'):
    with open(path, encoding='utf-8') as f:
        input_dict = json.load(f)
    print("Count: {}".format(len(input_dict)))


def get_candidates_unique_hashtags(path='candidates_timeline.json'):
    with open(path, encoding='utf-8') as f:
        input_dict = json.load(f)

    unique_hashtags = []

    for user_data in input_dict.values():
        hashtags = user_data['hashtags']
        [unique_hashtags.append(hashtag.lower()) for hashtag in hashtags]

    filtered_hashtags = []
    for h in unique_hashtags:
        add = True
        for f in ['psych', 'schizo', 'suic', 'ptsd', 'bipolar', 'mental', 'anxiet', 'depress', 'bpd', 'therapy',
                  'sicknotweak', 'thestigma', 'ocd', 'meds', 'medicat', 'trauma', 'mania']:
            if f in h:
                add = False
                break
        if add:
            filtered_hashtags.append(h)

    hashtags_counter = Counter(filtered_hashtags).most_common()[:200]

    print("Unique hashtags: {}/{}".format(len(hashtags_counter), len(unique_hashtags)))
    print(','.join([m[0] for m in hashtags_counter]))


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--count', action="store_true", default=False, dest='c')
    parser.add_option('--path_c', action="store", default='candidates_filtered_in.json')
    parser.add_option('-u', '--unique_hashtags', action="store_true", default=False, dest='u')
    parser.add_option('--path_u', action="store", default='candidates_timeline.json')
    options, remainder = parser.parse_args()

    if options.c:
        count_candidates_filtered_in(options.path_c)
    if options.u:
        get_candidates_unique_hashtags(options.path_u)
