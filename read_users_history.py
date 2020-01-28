import json
import os
import time
from argparse import ArgumentParser

import tweepy
import yaml

from data.skip_users import SKIP_USERS


class UserTweetFetcher:
    def __init__(self, config_path, save_path, users_paths, num_tweets, raw_data):
        self._api = None
        self._num_tweets = num_tweets
        self._config_path = config_path
        self._save_path = save_path
        self._users_paths = users_paths
        self._raw_data = raw_data
        self._users_written = 0
        self._users_tweets = {}

    def create_api(self):
        with open(self._config_path) as f:
            oauth_config = yaml.load(f, Loader=yaml.FullLoader)
        info = oauth_config['profiles']['user']
        info = info[list(info.keys())[0]]
        consumer_key = info['consumer_key']
        consumer_secret = info['consumer_secret']
        access_token = info['token']
        access_token_secret = info['secret']

        # Authorization to consumer key and consumer secret
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

        # Access to user's access key and access secret
        auth.set_access_token(access_token, access_token_secret)

        # Calling api
        self._api = tweepy.API(auth)

    @staticmethod
    def _read_twitter_raw_data(json_path):
        users = []
        with open(json_path) as f:
            for user in f:
                try:
                    user_json = json.loads(user)
                    users.append(user_json['user']['id_str'])
                except KeyError:
                    pass
                except json.decoder.JSONDecodeError:
                    pass
        return users

    @staticmethod
    def _read_twitter_user_json(json_path):
        with open(json_path) as f:
            users = json.load(f)
        return users.keys()

    def _load_cache(self):
        if os.path.isfile(self._save_path):
            with open(self._save_path) as f:
                self._users_tweets = json.load(f)

    def save_users(self):
        with open(self._save_path, 'w', encoding='utf-8') as out:
            print('Saving {} user entries'.format(len(self._users_tweets)))
            json.dump(self._users_tweets, out)

    def get_tweets(self):
        self._load_cache()
        users_list = []
        for user in self._users_paths:
            if self._raw_data:
                users_list.extend(self._read_twitter_raw_data(user))
            else:
                users_list.extend(self._read_twitter_user_json(user))

        print('Getting tweets from {} users'.format(len(users_list)))
        for user_id in users_list:
            # no need to use api if we already have tweets for this user
            if user_id in SKIP_USERS:
                continue
            if user_id not in self._users_tweets:
                self.get_user_tweets(user_id)

    def _get_user_timeline(self, user_id, count, max_id=None):
        """
        Use Twitter api to receive a users timeline posts.
        In addition to these input parameters, since we're only interested in posts, the api is used with:
        exclude_replies: when set to True, prevents replies from appearing in the returned timeline
        include_rts: when set to False, the timeline will strip any native retweets
        :param user_id: Twitter id of the user
        :param count: maximum posts
        :param max_id: maximum post id number when using the api several times on the same user
        :return: list of tweets from user timeline
        """
        try:
            if max_id:
                tweets = self._api.user_timeline(user_id=user_id, count=count, exclude_replies=True, include_rts=False,
                                                 tweet_mode="extended", max_id=max_id)
            else:
                tweets = self._api.user_timeline(user_id=user_id, count=count, exclude_replies=True, include_rts=False,
                                                 tweet_mode="extended")
        except tweepy.TweepError:
            tweets = None
        return tweets

    def get_user_tweets(self, user_id):
        """
        extract a user's recent timeline (200 recent tweets)
        :return: list of user tweets info
        """
        english_tweets = []
        new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets)

        while not new_tweets:
            response = self._api.last_response
            response_text = response.text
            if 'error' in response_text:
                if 'Rate limit exceeded' in response_text:
                    time.sleep(5)
                    new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets)
                else:
                    print("Skipping user {}".format(user_id))
                    return
            if 'Rate limit exceeded' in response_text or \
                    'rate_limit_context' in response_text and \
                    json.loads(response_text)['resources']['statuses']['/statuses/user_timeline']['remaining'] < 10:
                print("Going to sleep for 10 minutes because we reached api rate limit")
                time.sleep(10*60)
                new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets)
            if not new_tweets:
                print("Skipping user {}".format(user_id))
                return

        # keep grabbing tweets until we have enough
        while new_tweets and len(new_tweets) > 0 and len(english_tweets) < self._num_tweets:
            # skip non-English tweets
            english_tweets.extend([tweet for tweet in new_tweets if tweet.lang == 'en'])

            # we have enough good tweets, no need for more api calls
            if len(english_tweets) >= self._num_tweets:
                break

            # all subsequent requests use the max_id param to prevent duplicates
            oldest = new_tweets[-1].id - 1
            new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets*1.5, max_id=oldest)

        if len(english_tweets) < self._num_tweets:
            print("Skipping user {user_id} which has {tweet_count}/{tweet_threshold} valid tweets".format(
                user_id=user_id, tweet_count=len(english_tweets), tweet_threshold=self._num_tweets))
            return

        self.init_new_user(user_id)

        for tweet in english_tweets[:self._num_tweets]:
            tweet_text = tweet.full_text.lower()
            hashtags = [hashtag['text'] for hashtag in tweet.entities['hashtags']]

            if tweet_text:
                created_at = tweet.created_at.timestamp()
                self._users_tweets[user_id]['posts'].append((created_at, tweet_text))
            self._users_tweets[user_id]['hashtags'].extend(hashtags)

        print('Finished with user {}'.format(user_id))
        self._users_written += 1

        if self._users_written % 200 == 0:
            print('Saving after finished 200 users')
            self.save_users()

    def init_new_user(self, user_id):
        if user_id not in self._users_tweets:
            self._users_tweets[user_id] = {
                'posts': [],
                'hashtags': []
            }


if __name__ == '__main__':
    parser = ArgumentParser(prefix_chars='--')
    parser.add_argument('--users_paths', type=str, default='candidates.json', nargs='+',
                        help='Optional users path. This is the json file containing diagnosed schizophrenia users')
    parser.add_argument('--save_path', type=str, default='candidates_timeline.json',
                        help='Optional save path. If this file already exists it is reloaded to avoid unnecessary work')
    parser.add_argument('--oauth_config', type=str, default='config/oauth_config', help='Optional config file')
    parser.add_argument('--num_tweets', type=int, default=200, help='Minimum number of tweets per user')
    parser.add_argument('--raw_data', action='store_true', default=False,
                        help='Whether users_paths are with json format or raw format which is a list of jsons')
    options = parser.parse_args()

    tweet_fetcher = UserTweetFetcher(
        config_path=options.oauth_config,
        save_path=options.save_path,
        users_paths=options.users_paths,
        num_tweets=options.num_tweets,
        raw_data=options.raw_data
    )
    tweet_fetcher.create_api()

    try:
        tweet_fetcher.get_tweets()
    finally:
        tweet_fetcher.save_users()
        print("Finished")
