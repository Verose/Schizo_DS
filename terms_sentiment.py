import re


class TermSentiment:
    def __init__(self):
        self._positive_terms = self.load_positive_patterns()
        self._negative_terms = self.load_negative_patterns()

    @staticmethod
    def load_positive_patterns():
        with open('config/positive_patterns.txt') as f:
            positive_patterns = f.read().splitlines()
        return positive_patterns

    @staticmethod
    def load_negative_patterns():
        with open('config/negative_patterns.txt') as f:
            negative_patterns = f.read().splitlines()
        return negative_patterns

    def contains_positive_terms(self, tweet_text):
        for positive_term in self._positive_terms:
            if re.findall(positive_term, tweet_text):
                return True
        return False

    def contains_negative_terms(self, tweet_text):
        for negative_term in self._negative_terms:
            if re.findall(negative_term, tweet_text):
                return True
        return False
