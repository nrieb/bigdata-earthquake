#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from twython import Twython, TwythonError
import json
import time
import sys

import logging

# 180 times in 15 min
REQUEST_INTERVAL = (15*60) / 180.0

def get_auth(filename):
    auth = None
    with open(filename, "r") as auth_file:
        for line in auth_file:
            line = line.strip()
            if len(line):
                auth = json.loads(line)

    return auth

def make_obj():
    auth = get_auth("auth.txt")
    t = Twython(auth["consumer_key"],
                auth["consumer_secret"],
                auth["oauth_token"],
                auth["oauth_token_secret"])
    return t

def cursor(self, function, **params):

    if not hasattr(function, 'iter_mode'):
        raise TwythonError('Unable to create generator for Twython \
        method "%s"' % function.__name__)

    while True:
        min_id = None
        content = function(**params)

        if not content:
            raise StopIteration

        if hasattr(function, 'iter_key'):
            results = content.get(function.iter_key)
        else:
            results = content

        for result in results:
            if "id" in result and (min_id == None or result["id"] < min_id):
                min_id = result["id"]
            yield result

        if function.iter_mode == 'cursor' and \
           content['next_cursor_str'] == '0':
            raise StopIteration

        try:
            if function.iter_mode == 'id':
                if min_id != None:
                    params['max_id'] = min_id - 1
                else:
                    raise StopIteration
            elif function.iter_mode == 'cursor':
                params['cursor'] = content['next_cursor_str']
        except (TypeError, ValueError):  # pragma: no cover
            raise TwythonError('Unable to generate next page of search \
            results, `page` is not a number.')

def main():
    logging.basicConfig(level=logging.INFO)
    t = make_obj()
    def sleeper_search(**params):
        logging.info(params)
        result = t.search(**params)
        time.sleep(REQUEST_INTERVAL)
        return result
    sleeper_search.iter_mode = 'id'
    sleeper_search.iter_key = 'statuses'
    sleeper_search.iter_metadata = 'search_metadata'
    # NZ 6.7 http://earthquake.usgs.gov/earthquakes/eventpage/usc000sxye
    #results = cursor(t, sleeper_search, q="earthquake", count="100", geocode="-37.682,179.685,250km")
    # Indonesia 7.1 http://earthquake.usgs.gov/earthquakes/eventpage/usc000sxh8
    #results = cursor(t, sleeper_search, q='"earthquake"OR"gempa bumi"', count="100", geocode="1.928,126.547,250km")
    # Kansas 4.8 http://earthquake.usgs.gov/earthquakes/eventpage/usc000swru
    #results = cursor(t, sleeper_search, q="earthquake", count="100", geocode="37.275,-97.616,250km")
    #Greece 5.4 2014-11-17 16:05:57 UTC-07:00 and 5.3 2014-11-17 16:09:04 UTC-07:00
    # 5.4 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000syak
    # 5.3 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000syb1
    #results = cursor(t, sleeper_search, q='"earthquake"OR"σεισμός"', count="100", geocode="38.696,23.416,250km")
    # S. Japan 5.1 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000syw5
    # S. Japan 5.0 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000syhr
    #results = cursor(t, sleeper_search, q='"earthquake"OR"地震"OR"アースクェイク"', count="100", geocode="30.030,131.158,250km")
    # Iceland 5.2 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000sx8r
    # Iceland 5.1 http://comcat.cr.usgs.gov/earthquakes/eventpage/usc000sxqj
    #results = cursor(t, sleeper_search, q='"earthquake"OR"jarðskjálfta"', count="100", geocode="64.629,-17.728,250km")
    # N. Cal 4.2 http://earthquake.usgs.gov/earthquakes/eventpage/nc72350156
    results = cursor(t, sleeper_search, q='"earthquake"', count="100", geocode="36.809,-121.535,250km")
    for result in results:
        print(json.dumps(result))

                           
if __name__ == "__main__":
    main()
