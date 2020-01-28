import argparse
import json
from multiprocessing import Manager
from multiprocessing.pool import Pool
from tqdm import tqdm

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from preprocess_tweets import Patterns
from terms_sentiment import TermSentiment

user_id_to_matching_controls = {}


SCHIZO_WORDS = ["schizophrenia", "schizophrenic", "paranoid schizophrenia", "paranoid schizophrenic", "schiizophrenia",
                "schitzo", "schitzophrenia", "schizo", "schizofrenia", "schizophernia", "schizophren", "schizophrene",
                "schizophrenia", "schizophrenia disorder", "schizophreniak", "schizophrenic", "schizophrenic dis",
                "schizophrenic disorder", "schizophrenic narcissism", "schyzophrenia", "scizophrenia", "shizophrenia",
                "shizophrenic", "skitsafrantic", "skitzafrenic", "skitzophrenia", "unspecified schizophrenia"]


def insert_user_to_output_json(user_id, label, posts, out_json):
    # skip users (controls) which are already in
    if user_id in output_dataset:
        return

    out_json.append({
        "id": user_id,
        "label": [label],
        "posts": [{"text": post} for post in posts]
    })


posts = []
group_dict = []


def init(*args):
    global posts
    global group_dict
    posts = args[0]
    group_dict = args[1]


def get_posts(*args):
    index, (user_id, user_history) = args[0]
    user_posts = [p[1] for p in user_history["posts"][:100]]
    user_preprocessed_posts = [Patterns.preprocess(post) for post in user_posts]
    sentiment = TermSentiment()
    user_preprocessed_filtered_posts = [post for post in user_preprocessed_posts
                                        if not sentiment.contains_positive_terms(post) and post not in SCHIZO_WORDS]
    group_dict[index] = (user_id, user_preprocessed_filtered_posts)
    posts.append('\n'.join([p.strip() for p in user_preprocessed_filtered_posts]))


def read_group_posts(history_files, group_dict):
    """
    Each user is represented by a list of strings which are their posts.
    The posts go through preprocessing.
    :param history_files: a list of paths to group Twitter history file
    :param group_dict: group dictionary to insert the preprocessed posts to
    :return: List of lists representing a list of user posts
    """
    posts = manager.list()

    def update(*args):
        pbar.update()

    last_index = 0
    for hist_file in history_files:
        with open(hist_file) as f:
            hist = json.load(f)
        pool = Pool(processes=6, initializer=init, initargs=(posts, group_dict))
        indices = range(last_index, last_index+len(hist))
        pbar = tqdm(zip(indices, hist.items()), total=len(hist.items()), desc='Reading {}'.format(hist_file))
        for item in zip(indices, hist.items()):
            pool.apply_async(get_posts, args=(item,), callback=update)
        last_index = item[0]+1
        pool.close()
        pool.join()
        pbar.close()
    return posts


def get_similar_controls(schizo_ind, schizo_vec):
    similarities = cosine_similarity(schizo_vec, tfidf_controls)
    sorted_similarities = similarities[0].argsort()[:-args.matching_controls_cnt-1: -1]
    filtered_sorted_similarities = [sim for sim in sorted_similarities if similarities[0][sim] > 0.2]
    matching_controls_num = len(filtered_sorted_similarities)

    if matching_controls_num < 5:
        print("Skipping {} controls for user {}".format(matching_controls_num, schizos_dict[schizo_ind][0]))

    sorted_controls_posts = [controls_dict[ind] for ind in sorted_similarities]
    schizo_user = schizos_dict[schizo_ind]
    insert_user_to_output_json(schizo_user[0], 'schizophrenia', schizo_user[1], output_dataset)
    [insert_user_to_output_json(control_user[0], 'control', control_user[1], output_dataset)
     for control_user in sorted_controls_posts]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prefix_chars='--')
    parser.add_argument('--schizos', type=str, nargs='+', required=True, help='Schizophrenics Twitter history file')
    parser.add_argument('--controls', type=str, nargs='+', required=True, help='Controls Twitter history file')
    parser.add_argument('--n_processes', type=int, default=1, help='How many processes to use for runtime speedup')
    parser.add_argument('--matching_controls_cnt', type=int, default=7, help='How many controls to match each schizo')
    args = parser.parse_args()

    n_processes = args.n_processes
    controls_history_file = args.controls
    schizos_history_file = args.schizos

    all_hist = []
    manager = Manager()
    controls_dict = manager.dict()
    schizos_dict = manager.dict()

    controls_hist = read_group_posts(controls_history_file, controls_dict)
    schizos_hist = read_group_posts(schizos_history_file, schizos_dict)
    all_hist.extend(controls_hist)
    all_hist.extend(schizos_hist)

    controls_cnt = len(controls_hist)
    tfidf = TfidfVectorizer().fit_transform(all_hist)
    tfidf_controls = tfidf[0:controls_cnt]
    tfidf_schizos = tfidf[controls_cnt:]

    output_dataset = []
    for schizo_ind, schizo_vec in tqdm(enumerate(tfidf_schizos), total=tfidf_schizos.shape[0],
                                       desc='Finding similar controls for schizophrenics'):
        get_similar_controls(schizo_ind, schizo_vec)

    with open("tssd", 'w', encoding='utf-8') as out:
        for row in output_dataset:
            json.dump(row, out)
            out.write("\n")
