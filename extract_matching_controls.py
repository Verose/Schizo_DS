import argparse
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess_tweets import Patterns

user_id_to_matching_controls = {}


def insert_user_to_output_json(user_id, label, posts, out_json):
    # skip users (controls) which are already in
    if user_id in output_json:
        return
    out_json[user_id] = {
        'label': label,
        'posts': posts
    }


def read_group_posts(history_file, group_dict):
    """
    Each user is represented by a list of strings which are their posts.
    The posts go through preprocessing.
    :param history_file: path to group Twitter history file
    :param group_dict: group dictionary to insert the preprocessed posts to
    :return: List of lists representing a list of user posts
    """
    with open(history_file) as f:
        hist = json.load(f)

    posts = []
    for index, (user_id, user_history) in enumerate(hist.items()):
        user_posts = [p[1] for p in user_history["posts"]]
        user_preprocessed_posts = [Patterns.preprocess(post) for post in user_posts]
        group_dict[index] = (user_id, user_preprocessed_posts)
        posts.append('\n'.join([p.strip() for p in user_preprocessed_posts]))
    return posts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prefix_chars='--')
    parser.add_argument('--schizos', type=str, required=True, help='Schizophrenics Twitter history file')
    parser.add_argument('--controls', type=str, required=True, help='Controls Twitter history file')
    parser.add_argument('--matching_controls_cnt', type=int, default=5, help='How many controls to match each schizo')
    args = parser.parse_args()

    controls_history_file = args.controls
    schizos_history_file = args.schizos

    all_hist = []
    controls_dict = {}
    schizos_dict = {}

    controls_hist = read_group_posts(controls_history_file, controls_dict)
    schizos_hist = read_group_posts(schizos_history_file, schizos_dict)
    all_hist.extend(controls_hist)
    all_hist.extend(schizos_hist)

    controls_cnt = len(controls_hist)
    tfidf = TfidfVectorizer().fit_transform(all_hist)
    tfidf_controls = tfidf[0:controls_cnt]
    tfidf_schizos = tfidf[controls_cnt:]

    output_json = {}

    # cosine_similarity(tfidf_schizos, tfidf_controls)
    for schizo_ind, schizo_vec in enumerate(tfidf_schizos):
        similarities = cosine_similarity(schizo_vec, tfidf_controls)
        sorted_similarities = similarities[0].argsort()[:-args.matching_controls_cnt: -1]
        # todo: filter by a minimum cosine score and delete schizos with not enough controls
        sorted_controls_posts = [controls_dict[ind] for ind in sorted_similarities]
        schizo_user = schizos_dict[schizo_ind]
        insert_user_to_output_json(schizo_user[0], 'schizophrenia', schizo_user[1], output_json)
        [insert_user_to_output_json(control_user[0], 'control', control_user[1], output_json)
         for control_user in sorted_controls_posts]

    with open("tssd.json", 'w', encoding='utf-8') as out:
        json.dump(output_json, out)
