#!/usr/bin/env python
"""
Takes an earthquake time and a list of tweets with created_at attirbutes and
returns the tweets that are 2 hours before the time or 4 hours after the time.
"""


from __future__ import print_function

import sys
import json
from datetime import datetime, timedelta

# 2014-11-20 06:26:49 UTC
INPUT_FORMAT = "%Y-%m-%d %H:%M:%S"
#"Wed Nov 19 23:15:11 +0000 2014"
TWEET_FORMAT = "%a %b %d %H:%M:%S +0000 %Y"

#   date_timely :: Datetime -> Datetime -> Bool
def date_timely(time1, time2):
    """
    Returns whether time1 is in a predifined interval around time2
    """
    diff = abs(time2 - time1)
    before = timedelta(hours=2)
    after = timedelta(hours=4)
    if time1 < time2:
        return diff <= before
    else: # time1 >= time2
        return diff <= after

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
    for tweet in timely_data(sys.stdin, earthquake_time):
        print(json.dumps(tweet))

if __name__ == "__main__":
    main()

