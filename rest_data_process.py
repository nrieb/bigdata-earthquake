#!/usr/bin/env python
"""
Takes an earthquake time and a list of tweets with created_at attirbutes and
returns the tweets that are 2 hours before the time or 4 hours after the time.
"""


from __future__ import print_function

import sys
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from nltk import PorterStemmer
from nltk.corpus import stopwords

# 2014-11-20 06:26:49 UTC
INPUT_FORMAT = "%Y-%m-%d %H:%M:%S"
#"Wed Nov 19 23:15:11 +0000 2014"
TWEET_FORMAT = "%a %b %d %H:%M:%S +0000 %Y"
'''--------------------------------------------------------------------------'''
'''WordCount'''
'''--------------------------------------------------------------------------'''
#   english_transform :: String -> String
def english_transform(word):
    lowercase = word.lower()
    stemmer = PorterStemmer()
    stemmed = stemmer.stem(lowercase)
    if lowercase in stopwords.words('english') or \
       stemmed in stopwords.word('english') or stemmed == "earthquake":
        return ""
    else:
        return stemmed

#   wordcount :: [Dict] -> (String -> String) -> {String:Int}
def wordcount(tweets, word_transform):
    words = {}
    for tweet in tweets:
        if "text" in tweet:
            text = tweet["text"]
        else:
            continue
        for word in (word_transform(x) for x in text.split(' ') if len(word_transfom(x))):
            if word in words:
                words[word] += 1
            else:
                words[word] = 1
    return words

#   split_tweets_by_lang :: [Dict] -> {String:[Dict]}
def split_tweets_by_lang(tweets):
    langs = {}
    for tweet in tweets:
        if "lang" in tweet:
            lang = tweet["lang"]
        else:
            lang = "other"
        if lang in langs:
            langs[lang].append(tweet)
        else:
            langs[lang] = [tweet]

    return langs

#   wordcounts_by_lang :: [Dict] -> {Lang:{Word:Count}}
def wordcounts_by_lang(tweets):
    wordcounts = {}
    tweets_by_lang = split_tweets_by_lang(tweets)
    for lang, tweets in tweets_by_lang.iteritems():
        if lang == "en":
            wordcounts[lang] = wordcount(tweets, english_transform)
        else:
            wordcounts[lang] = wordcount(tweets, lambda x: x.lower())
    return wordcounts

'''--------------------------------------------------------------------------'''
'''Graph'''
'''--------------------------------------------------------------------------'''
#   datetime_ceil_by_hour :: Datetime -> Datetime
def datetime_ceil_by_hour(date_time):
    if date_time.minute or date_time.second or date_time.microsecond:
        return date_time.replace(second=0, microsecond=0) + timedelta(hours=1)
    else:
        return date_time

#   datetime_interval_by_hours :: Datetime -> Datetime -> Timedelta -> [(Datetime, Datetime)]
def datetime_buckets(low, high, interval):
    assert low < high
    dates = [low]
    curr_date = low
    while curr_date + interval < high:
        curr_date += interval
        dates.append(curr_date)
    return zip(dates[:-1], dates[1:])

def in_bucket(value, (low, high)):
    return low <= value < high

#   num_dates_in_buckets :: [Dict] -> [(Datetime, Datetime)] -> [Int]
def num_dates_in_buckets(dates, buckets):
    assert len(buckets) > 1
    #dates = sorted((datetime.strptime(x["created_at"], TWEET_FORMAT)
    #                for x in tweets))
    curr_bucket = 0
    count = 0
    counts = []
    date = 0
    while date < len(dates) and curr_bucket < len(buckets):
        if in_bucket(dates[date], buckets[curr_bucket]):
            count += 1
            date += 1
        else:
            counts.append(count)
            count = 0
            curr_bucket += 1

    return counts


def graph_tweets(tweets):
    dates = sorted((datetime.strptime(x["created_at"], TWEET_FORMAT)
                    for x in tweets))
    low = min(dates).replace(second=0, microsecond=0)
    high = datetime_ceil_by_hour(max(dates))
    #buckets = datetime_buckets(low, high, timedelta(hours=1))
    buckets = datetime_buckets(low, high, timedelta(minutes=15))
    count_per_bucket = num_dates_in_buckets(dates, buckets)
    # graph it. # is y axis, buckets are x axis, count_per bucket is the bar
    plt.clf()
    plt.bar(range(len(count_per_bucket)), count_per_bucket,
            color='r', label='# of tweets')
    plt.title("Japan - 6.2 - 2014-11-22 13:08:18 UTC")
    plt.xlabel("Time Intervals")
    plt.ylabel("Count of Tweets")
    plt.xticks(range(len(buckets)),
               ["{0}:{1:02}".format(x.hour, x.minute) for (x,_) in buckets],
               rotation='vertical')
    plt.show()
    #plt.savefig("japan_6.2.png")

'''--------------------------------------------------------------------------'''
''' Relevant Tweets '''
'''--------------------------------------------------------------------------'''
#   unique_tweets :: [Dict] -> [Dict]
def unique_tweets(tweets):
    sorted_by_id = sorted((x for x in tweets if "id" in x),
                          cmp=lambda x,y: cmp(x["id"], y["id"]))
    uniques = []
    prev_tweet = None
    for tweet in sorted_by_id:
        if prev_tweet == None or prev_tweet["id"] != tweet["id"]:
            uniques.append(tweet)
        prev_tweet = tweet

    return uniques
    
#   date_timely :: Datetime -> Datetime -> Bool
def date_timely(time1, time2):
    """
    Returns whether time1 is in a predifined interval around time2
    """
    diff = time2 - time1
    before = timedelta(hours=2)
    after = timedelta(hours=4)
    return time2 - before <= time1 <= time2 + after

#   tweet_timely :: Dict -> Datetime -> Bool
def tweet_timely(tweet, time):
    """
    Returns whether the tweet is in a predifined interval around time.
    """
    if "created_at" not in tweet:
        return False
    else:
        try:
            created_at = datetime.strptime(tweet["created_at"], TWEET_FORMAT)
            return date_timely(created_at, time)
        except ValueError:
            return False

#   timely_data :: File -> Datetime -> IO (Dict)
def timely_data(file_obj, earthquake_time):
    """
    Looks in the file object for data around the earthquake_time.
    """
    data = []
    for line in file_obj:
        line = line.strip()
        if len(line):
            try:
                tweet = json.loads(line)
            except ValueError:
                continue
            if tweet_timely(tweet, earthquake_time):
                data.append(tweet)
    return unique_tweets(data)

'''--------------------------------------------------------------------------'''
#   main :: IO()
def main():
    """
    main
    """

    args = sys.argv[1:]
    if len(args) < 1:
        print("Need 1 argument")
        return

    try:
        earthquake_time = datetime.strptime(args[0], INPUT_FORMAT)
    except ValueError:
        print("Need baseline time in XXX format")
        return
    """
    for tweet in timely_data(sys.stdin, earthquake_time):
        print(json.dumps(tweet))
    
    tweets = []
    for line in sys.stdin:
        line = line.strip()
        if len(line):
            tweets.append(json.loads(line))
    graph_tweets(tweets)
    """
    graph_tweets(timely_data(sys.stdin, earthquake_time))

if __name__ == "__main__":
    main()

