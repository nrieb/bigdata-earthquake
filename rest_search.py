#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from twython import Twython, TwythonError
import json
import time
import sys
from datetime import datetime, timedelta
from collections import namedtuple
import os.path

import logging

# 180 times in 15 min
REQUEST_INTERVAL = (15*60) / 180.0

'''--------------------------------------------------------------------------'''
'''USGS data handling'''
'''--------------------------------------------------------------------------'''
# data Magnitude = Float
#   date_mag_from_prop :: Dict -> (Datetime, Magnitude)
def date_mag_from_prop(prop):
    """Retrieve the time and decode it into datetime.  Also get the earthquake
    magnitude"""
    assert "time" in prop
    assert "mag" in prop
    # epoc_sec :: Sec 1
    epoc_sec = prop["time"] / 1000.0 #Assumed to be in UTC
    prop_date = datetime.utcfromtimestamp(epoc_sec)
    mag = prop["mag"]
    return (prop_date, mag)

# data Lat = Float
# data Lon = Float
#   lat_lon_from_geom :: Dict -> (Lat, Lon)
def lat_lon_from_geom(geometry):
    """Get the Lat/Lon from the geometry"""
    assert "type" in geometry
    assert "coordinates" in geometry
    assert geometry["type"] == "Point"
    lat = geometry["coordinates"][1]
    lon = geometry["coordinates"][0]
    return (lat, lon)

Quake = namedtuple("Quake", ["lat", "lon", "mag", "date"])
#   quakes_from_usgs_data :: [Dict] -> [Quake]
def quakes_from_usgs_data(earthquakes):
    """Extract relevant information from the earthquake features"""
    eq_data = []
    for earthquake in earthquakes:
        assert "properties" in earthquake
        (prop_date, magnitude) = date_mag_from_prop(earthquake["properties"])
        assert "geometry" in earthquake
        (lat, lon) = lat_lon_from_geom(earthquake["geometry"])
        eq_data.append(Quake(lat=lat, lon=lon, mag=magnitude, date=prop_date))
    return eq_data

#   earthquakes_from_file :: Filename -> IO([Quake])
def earthquakes_from_file(filename):
    data = None
    with open(filename, "r") as usgs_file:
        data = json.load(usgs_file)
    assert "features" in data
    return quakes_from_usgs_data(data["features"])

'''--------------------------------------------------------------------------'''
'''Twitter handling'''
'''--------------------------------------------------------------------------'''
#   query_params :: Lat -> Lon -> Datetime -> Dict
def query_params(lat, lon, date):
    """construct the extra query parameters"""
    params = {}
    until_day = date + timedelta(days=2)
    params["q"] = "earthquake"
    params["count"] = 100
    params["geocode"] = "{lat},{lon},250km".format(lat=lat, lon=lon)
    params["until"] = until_day.strftime("%Y-%m-%d")
    return params

def earthquake_filename(quake):
    date_string = quake.date.strftime("%Y-%m-%d_%H:%M:%S")
    return "{mag}_{lat}_{lon}_{date}.json".format(mag=quake.mag,
                                                  lat=quake.lat,
                                                  lon=quake.lon,
                                                  date=date_string)

#   get_auth :: Filename -> IO (Dict)
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
        max_id = None
        content = function(**params)

        if not content:
            raise StopIteration

        if hasattr(function, 'iter_key'):
            results = content.get(function.iter_key)
        else:
            results = content
        logging.info("retrived {0}".format(len(results)))
        for result in results:
            if "id" in result:
                if min_id == None or result["id"] < min_id:
                    min_id = result["id"]
                if max_id == None or result["id"] > max_id:
                    max_id = result["id"]
            yield result

        logging.info("max_id {0}".format(max_id))
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
    args = sys.argv[1:]
    if len(args) < 2:
        logging.error("not enough arguments")
        return
    quake_file = args[0]
    data_dir = args[1]
    quakes = earthquakes_from_file(quake_file)
    twitter = make_obj()
    def sleeper_search(**params):
        logging.info(params)
        result = twitter.search(**params)

        time.sleep(REQUEST_INTERVAL)
        return result
    sleeper_search.iter_mode = 'id'
    sleeper_search.iter_key = 'statuses'
    sleeper_search.iter_metadata = 'search_metadata'
    for quake in quakes:
        params = query_params(quake.lat, quake.lon, quake.date)
        filename = earthquake_filename(quake)
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath) or quake.date < (datetime.utcnow() - timedelta(days=10)):
            continue # don't re-look for ones we've found or from 10 days ago
        results = cursor(twitter, sleeper_search, q=params["q"],
                         count=params["count"], geocode=params["geocode"])
    #until=params["until"])
        result_list = [x for x in results]
        if len(result_list):
            with open(filepath, "w") as quake_file:
                for result in result_list:
                    quake_file.write(json.dumps(result))
                    quake_file.write("\n")


def main_old():
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
    #results = cursor(t, sleeper_search, q='"earthquake"', count="100", geocode="36.809,-121.535,250km")
    # 6.2 Japan http://earthquake.usgs.gov/earthquakes/eventpage/usb000syza
    #results = cursor(t, sleeper_search, q='"earthquake"OR"地震"OR"アースクェイク"', count=100, geocode="36.64,137.911,250km", until="2014-11-23", min_id="535567492274331648")
    #results = cursor(t, sleeper_search, q='', count="100", geocode="36.64,137.911,250km", until="2014-11-23")
    # texas 3.3 http://earthquake.usgs.gov/earthquakes/eventpage/usb000sz6q
    #results = cursor(t, sleeper_search, q='earthquake', count="100", geocode="32.836,-96.892,250km", until="2014-11-24")
    #
    results = cursor(t, sleeper_search, q='earthquake', count="100", geocode="32.836,-96.892,250km", until="2014-11-24")
    for result in results:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
