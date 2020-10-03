# Schizo_DS
This code creates a dataset named TSSD - Twitter Self-Reported Schizophrenia Diagnoses.  
The dataset collected here is used in [Semantic Characteristics of Schizophrenic Speech](https://github.com/Verose/NLP_CLPSYCH)  

We collected data using a Twitter filter API, separated into two groups:
- Self-reported schizophrenia spectrum disorders (schizophrenia)
- Control group: matched users who are similar to the schizophrenia group.

#### Diagnosed users: 
To create TSSD, we start by collecting a group of candidate schizophrenia users using
the Twitter filter API. For filtering, all kinds of synonyms of schizophrenia were used. We then apply two
types of high precision patterns: the first is used to match
a positive diagnoses, and the second to remove a negative diagnoses. These were manually reviewed and
verified. A further filtering removed users with fewer than 100 public English tweets.

#### Control users: 
After having a group of diagnosed users with their respective latest 100 posts, we selected
the most used 200 words, excluding stop words and mental-health related words, as a new filter for Twitter’s
filter API. As before, users with less than 100 public English tweets were filtered out. For each diagnosed
user, a group of up to 7 most similar controls users were selected based on their posts cosine similarity
scores. Only users passing a 0.2 cosine similarity score threshold were eligible for inclusion. Note that the
final dataset does not include duplicate users nor posts related to mental health.

## High Level Design and Flow

![Speech Social Media Design](./Social%20Media%20-%20TSSD.png)
