import argparse
import json
import logging
import time

from terms_sentiment import TermSentiment


class SchizophreniaCandidates:
    def __init__(self, input_files, log_file, output_file):
        self._sentiment = TermSentiment()
        self._input_files = input_files
        self._output_file = output_file
        self._logger = logging.getLogger('schizo_db')
        self._users = {}

        # Setup logger
        self._logger.setLevel(logging.DEBUG)

        # Create handlers
        stdout_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(log_file, encoding='utf-8')

        # Create formatters and add it to handlers
        stdout_handler.setFormatter(logging.Formatter('%(message)s'))
        file_handler.setFormatter(logging.Formatter('%(message)s'))

        # Add handlers to the logger
        self._logger.addHandler(stdout_handler)
        self._logger.addHandler(file_handler)

    @staticmethod
    def filter_out_retweets(tweet):
        if 'quoted_status' in tweet or 'quoted_status_permalink' in tweet or 'retweeted_status' in tweet:
            return True
        return False

    @staticmethod
    def filter_out_adds(tweet_text):
        if 'http' in tweet_text:
            return True
        return False

    @staticmethod
    def filter_in_self_terms(tweet_text):
        for self_term in ['I ', 'i ', 'I\'m', 'i\'m', 'im', 'i\'ve', 'ive', 'me']:
            if self_term not in tweet_text:
                return False
        return True

    def find_schizo_candidates(self, high_precision=False):
        users = []

        for file in self._input_files:
            tweet_counter = 0

            with open(file, encoding='utf-8') as f:
                for line in f.read().splitlines():
                    if not line or not line.strip():
                        continue
                    if 'EOFError' in line:
                        continue

                    try:
                        tweet = json.loads(line, encoding='utf-8')
                    except json.decoder.JSONDecodeError:
                        continue
                    if self.filter_out_retweets(tweet):
                        continue

                    # prefer 'full_text', otherwise take 'text' minus the link at the end
                    tweet_text = tweet['extended_tweet']['full_text'] if 'extended_tweet' in tweet else tweet['text']
                    tweet_text = tweet_text.lower()

                    if self.filter_out_adds(tweet_text):
                        continue

                    if high_precision:
                        if not self._sentiment.contains_positive_terms(tweet_text):
                            continue
                        if self._sentiment.contains_negative_terms(tweet_text):
                            continue
                    else:
                        if self.filter_in_self_terms(tweet_text):
                            continue
                        if 'diagnos' not in tweet_text:
                            continue

                    user_id = tweet['user']['id']
                    created_at = tweet['created_at']
                    created_at = time.mktime(time.strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y"))
                    hashtags = tweet['entities']['hashtags']
                    hashtags = [hashtag['text'] for hashtag in hashtags]

                    if user_id not in self._users:
                        self._users[user_id] = {
                            'posts': [],
                            'hashtags': []
                        }
                    self._users[user_id]['posts'].append((created_at, tweet_text))
                    self._users[user_id]['hashtags'].extend(hashtags)

                    self._logger.info(tweet_text)
                    self._logger.info('-----------------------------------------------------------------')
                    tweet_counter += 1
                    users += [user_id]
            self._logger.info('*****************************************************************')
            self._logger.info('Found {counter} schizophrenia candidates in {file}'.format(
                counter=tweet_counter, file=file))
            self._logger.info('*****************************************************************')
        self._logger.info('Out of {} users, there are {} unique'.format(len(users), len(set(users))))

        with open(self._output_file, 'w', encoding='utf-8') as out:
            json.dump(self._users, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prefix_chars='--')
    parser.add_argument('--input', type=str, nargs='+', required=True, help='Input files to process')
    parser.add_argument('--log', type=str, default='candidates.txt', help='Optional log file')
    parser.add_argument('--output', type=str, default='candidates.json', help='Optional output file')
    parser.add_argument('-hp', '--high_precision', action='store_true', default=False,
                        help='Set this to perform a search for candidates using SMHD high precision patterns.')
    options = parser.parse_args()

    candidates = SchizophreniaCandidates(options.input, options.log, options.output)
    candidates.find_schizo_candidates(options.high_precision)
