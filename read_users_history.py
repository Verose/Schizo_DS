import json
import os
import re
from argparse import ArgumentParser

import tweepy
import yaml


class UserTweetFetcher:
    def __init__(self, config_path, save_path, users_path):
        self._api = None
        self._num_tweets = 200
        self._config_path = config_path
        self._save_path = save_path
        self._users_path = users_path
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
    def _read_twitter_user_json(json_path):
        with open(json_path) as f:
            users = json.load(f)
        return users

    def _load_cache(self):
        if os.path.isfile(self._save_path):
            with open(self._save_path) as f:
                self._users_tweets = json.load(f)

    def save_users(self):
        with open(self._save_path, 'w', encoding='utf-8') as out:
            json.dump(self._users_tweets, out)

    def get_tweets(self):
        self._load_cache()
        users_json = self._read_twitter_user_json(self._users_path)

        for user_id in users_json:
            # no need to use api if we already have tweets for this user
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
                                                 max_id=max_id)
            else:
                tweets = self._api.user_timeline(user_id=user_id, count=count, exclude_replies=True, include_rts=False)
        except tweepy.TweepError:
            tweets = None
        return tweets

    def get_user_tweets(self, user_id):
        """
        extract all tweets from a user's timeline in batches of size self._num_tweets from most recent to oldest
        :return: list of user tweets info
        """
        all_tweets = []
        new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets)
        self.init_new_user(user_id)

        if not new_tweets:
            print("Skipping user {} which probably has protected tweets".format(user_id))
            return

        # keep grabbing tweets until there are no tweets left to grab
        while len(new_tweets) > 0:
            all_tweets.extend(new_tweets)
            oldest = all_tweets[-1].id - 1
            # all subsequent requests use the max_id param to prevent duplicates
            new_tweets = self._get_user_timeline(user_id=user_id, count=self._num_tweets, max_id=oldest)
            if not new_tweets:
                break

        for tweet in all_tweets:
            # skip non-English tweets
            if tweet.lang != 'en':
                continue

            # remove the url at the end and convert to lowercase
            tweet_text = re.sub(r"http\S+$", "", tweet.text.lower())
            hashtags = tweet.entities['hashtags']
            hashtags = [hashtag['text'] for hashtag in hashtags]
            if tweet_text:
                created_at = tweet.created_at.timestamp()
                self._users_tweets[user_id]['posts'].append((created_at, tweet_text))
            self._users_tweets[user_id]['hashtags'].extend(hashtags)

        print('Finished with user {} with {} tweets'.format(user_id, len(self._users_tweets[user_id]['posts'])))

    def init_new_user(self, user_id):
        if user_id not in self._users_tweets:
            self._users_tweets[user_id] = {
                'posts': [],
                'hashtags': []
            }


if __name__ == '__main__':
    parser = ArgumentParser(prefix_chars='--')
    parser.add_argument('--users_path', type=str, default='candidates.json', help='Optional users path')
    parser.add_argument('--save_path', type=str, default='candidates_timeline.json', help='Optional save path')
    parser.add_argument('--oauth_config', type=str, default='config/oauth_config', help='Optional config file')
    options = parser.parse_args()

    tweet_fetcher = UserTweetFetcher(
        config_path=options.oauth_config,
        save_path=options.save_path,
        users_path=options.users_path
    )
    tweet_fetcher.create_api()

    try:
        tweet_fetcher.get_tweets()
    finally:
        tweet_fetcher.save_users()
        print("Finished")


# '__weakref__', '_api', '_json', 'author', 'contributors', 'coordinates', 'created_at', 'destroy', 'entities',
# 'favorite', 'favorite_count', 'favorited', 'geo', 'id', 'id_str', 'in_reply_to_screen_name', 'in_reply_to_status_id',
# 'in_reply_to_status_id_str', 'in_reply_to_user_id', 'in_reply_to_user_id_str', 'is_quote_status', 'lang', 'parse',
# 'parse_list', 'place', 'possibly_sensitive', 'retweet', 'retweet_count', 'retweeted', 'retweets', 'source',
# 'source_url', 'text', 'truncated', 'user']
# print(dir(user_timeline[0]))
