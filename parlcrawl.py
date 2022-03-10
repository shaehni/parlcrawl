#!/bin/python3

# Modules
import argparse
import json
import requests

# Global variables
api_url = 'http://ws-old.parlament.ch/'
lang = 'de'
version = '0.1'

# Parse arguments
ap = argparse.ArgumentParser(description='Parlcrawl v' + version)

ap.add_argument("affairid", type=int, help="Geschäfts-Nummer gemäss Curia Vista als ID (20212355) oder Kurzform ("
                                           "21.2355)")
args = ap.parse_args()


# Request JSON data via API
def get_json(affairid):
    global api_url, lang
    try:
        url = api_url + 'affairs/' + str(affairid) + '?format=json&lang=' + lang
        headers = {'Accept': 'text/json'}
        print('Verbinde: ' + url)
        r = requests.get(url, headers=headers)
    except:
        print('Verbindungsfehler 1.')
        return False

    if r.status_code == 200:
        return r.text
    else:
        print('Verbindungsfehler 2.')
        return False


# Start main function
def main():
    if args.affairid > 0:
        data_raw = get_json(args.affairid)
        data = json.loads(data_raw)
        print(data['updated'])
    else:
        print('Ungültige ID')


if __name__ == '__main__':
    main()
