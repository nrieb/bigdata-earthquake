#!/usr/bin/env python
from __future__ import print_function
import json
import sys

"""
remove lady gaga, panda, wrestling, sex
"""

def main():
    geo = 0
    count = 0
    for line in sys.stdin:
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
            if "text" in obj:
                print(obj["text"].encode('utf-8', 'ignore'))
                count += 1

            if "geo" in obj:
                print("geo: {0}".format(obj["geo"]))
                if obj["geo"] != None:
                    geo += 1
            """
            if "id" in obj:
                print(obj["id"])
            """
    print("count {0}, geo_count {1}".format(count, geo))

if __name__ == "__main__":
    main()
