import re


# def preprocess_tweet(text):
#     # Check characters to see if they are in punctuation
#     nopunc = [char for char in text if char not in string.punctuation]
#     # Join the characters again to form the string.
#     nopunc = ''.join(nopunc)
#     # convert text to lower-case
#     nopunc = nopunc.lower()
#     # remove URLs
#     nopunc = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))', '', nopunc)
#     nopunc = re.sub(r'http\S+', '', nopunc)
#     # remove usernames
#     nopunc = re.sub('@[^\s]+', '', nopunc)
#     # remove the # in #hashtag
#     nopunc = re.sub(r'#([^\s]+)', r'\1', nopunc)
#     # remove repeated characters
#     nopunc = word_tokenize(nopunc)
#     # remove stopwords from final word list
#     return [word for word in nopunc if word not in stopwords.words('english')]


# https://github.com/s/preprocessor/blob/master/preprocessor/


class Patterns:
    URL_PATTERN = re.compile(r"http\S+")
    HASHTAG_PATTERN = re.compile(r"#")
    MENTION_PATTERN = re.compile(r"@\w*")
    RESERVED_WORDS_PATTERN = re.compile(r"^(RT|FAV)")

    try:
        # UCS-4
        EMOJIS_PATTERN = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
    except re.error:
        # UCS-2
        EMOJIS_PATTERN = re.compile(
            u'([\u2600-\u27BF])|([\uD83C][\uDF00-\uDFFF])|([\uD83D][\uDC00-\uDE4F])|([\uD83D][\uDE80-\uDEFF])')

    SMILEYS_PATTERN = re.compile(r"(?:X|:|;|=)(?:-)?(?:\)|\(|O|D|P|S){1,}", re.IGNORECASE)
    NUMBERS_PATTERN = re.compile(r"(^|\s)(\-?\d+(?:\.\d)*|\d+)")
    PUNCTUATION_PATTERN = r"[:()-/,.;?!&$]+\ *"

    @staticmethod
    def preprocess_urls(tweet_string, repl):
        return Patterns.URL_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_hashtags(tweet_string, repl):
        return Patterns.HASHTAG_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_mentions(tweet_string, repl):
        return Patterns.MENTION_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_reserved_words(tweet_string, repl):
        return Patterns.RESERVED_WORDS_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_emojis(tweet_string, repl):
        return Patterns.EMOJIS_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_smileys(tweet_string, repl):
        return Patterns.SMILEYS_PATTERN.sub(repl, tweet_string)

    @staticmethod
    def preprocess_numbers(tweet_string, repl):
        return re.sub(Patterns.NUMBERS_PATTERN, lambda m: m.groups()[0] + repl, tweet_string)

    @staticmethod
    def preprocess_ascii_lowercase(tweet_string, repl):
        return tweet_string.encode('ascii', 'ignore').decode('ascii').lower()

    @staticmethod
    def _preprocess_punctuation(tweet_string, repl):
        return re.sub(Patterns.PUNCTUATION_PATTERN, " ", tweet_string)

    @staticmethod
    def preprocess(tweet_string):
        method_list = [func for func in dir(Patterns) if callable(getattr(Patterns, func))
                       and not func.startswith("_") and func != 'preprocess']

        for method in method_list:
            static_method = Patterns.__getattribute__(Patterns, method)
            actual_method = static_method.__get__(object)
            tweet_string = actual_method(tweet_string, "")

        tweet_string = Patterns._preprocess_punctuation(tweet_string, "")
        return tweet_string


print(Patterns.preprocess("bla/bla (he:he) https://bla test :) numbers 1948 so.another test. lol,    bla. fin!"))
