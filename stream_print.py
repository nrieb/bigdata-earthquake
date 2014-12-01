#!/usr/bin/env python
from __future__ import print_function
import json
import sys
import re

"""
remove lady gaga, panda, wrestling, sex
"""

def main():
    geo = 0
    count = 0
    retweet = 0
    earthquakes = sys.argv[1:]
    for earthquake in earthquakes:
        count = 0
        geo = 0
        retweet = 0
        with open(earthquake, "r") as eq_file:
            for line in eq_file:
                line = line.strip()
                if len(line):
                    try:
                        obj = json.loads(line)
                    except ValueError:
                        continue
                """
                print(sorted(obj.keys()))
                print(json.dumps(obj, sort_keys=True,
                indent=4, separators=(',', ': ')))
                """
                #if "text" in obj and re.match("^RT", obj["text"]):
                if "text" in obj:
                #print(json.dumps(obj, sort_keys=True, indent=4,
                #                 separators=(',', ': ')))
                #print("retweeted_status" in obj)
                    #print(obj["text"].encode('utf-8', 'ignore'))
                    count += 1
                
                if "retweeted_status" in obj or ("text" in obj and re.match("^RT", obj["text"])):
                    retweet += 1
                if "geo" in obj:
                    #print("geo: {0}".format(obj["geo"]))
                    if obj["geo"] != None:
                        geo += 1
            """
            if "id" in obj:
                print(obj["id"])
            """
            #print("count {0}, geo_count {1}, retweet {2}, file {3}".format(count, geo, retweet, eqarthquake))
            print("{0}\t{1}\t{2}".format(earthquake, geo, count))


if __name__ == "__main__":
    main()
