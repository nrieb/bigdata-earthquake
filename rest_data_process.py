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

# 2014-11-20 06:26:49 UTC
INPUT_FORMAT = "%Y-%m-%d %H:%M:%S"
#"Wed Nov 19 23:15:11 +0000 2014"
TWEET_FORMAT = "%a %b %d %H:%M:%S +0000 %Y"

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
    plt.title("Kansas - 4.8 - 2014-11-12 21:40:00 UTC")
    plt.xlabel("Time Intervals")
    plt.ylabel("Count of Tweets")
    plt.xticks(range(len(buckets)),
               ["{0}:{1:02}".format(x.hour, x.minute) for (x,_) in buckets],
               rotation='vertical')
    #plt.show()
    plt.savefig("kansas_4.8.png")

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
    Returns whther the tweet is in a predifined interval around time.
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
            tweet = json.loads(line)
            if tweet_timely(tweet, earthquake_time):
                data.append(tweet)
    return data

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
    """
    graph_tweets(timely_data(sys.stdin, earthquake_time))

if __name__ == "__main__":
    main()

