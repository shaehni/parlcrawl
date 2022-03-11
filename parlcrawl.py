#!/bin/python3

# Module
import argparse
import json
import os
import re
import requests

from datetime import datetime

# Globale Variablen
api_url = 'http://ws-old.parlament.ch/'
lang = 'de'
r1 = re.compile(r'\d{2}\.\d{3,4}')  # Format für Geschäftsnummern
r2 = re.compile(r'\d{8}')  # Format für Geschäfts-IDs
today = datetime.today()
version = '1.2'

# ArgumentParser
ap = argparse.ArgumentParser(usage='%(prog)s [-h] [-t Zeitraum] Geschäfts-Liste',
                             description='Parlcrawl v' + version,
                             epilog='\b')

ap.add_argument('listfile', type=argparse.FileType('r'), metavar='Geschäftsliste',
                help='Text-Datei mit Geschäftsnummern (eine pro Zeile) als ID (20212355) oder Kurzform (21.2355).')
ap.add_argument('--create-cache', action='store_true',
                help='Speichert die abgerufenen Daten lokal ab.')
ap.add_argument('--dry', action='store_true',
                help='Prüft nur die Dateiliste ohne Anfrage an die API.')
ap.add_argument('--from-cache', action='store_true',
                help='Liest Geschäftsdaten aus dem Cache anstelle der API.')
ap.add_argument('--ignore-done', action='store_true',
                help='Blendet Information aus, wenn Geschäfte erledigt sind.')
ap.add_argument('-t', type=int, default=7, metavar='Tage',
                help='Zeitraum, für den geänderte Vorstösse angezeigt werden (Standard: 7).')
args = ap.parse_args()


# Lade Geschäftsliste
def load_affairs(list_file):
    global r1, r2
    affairs_list = []

    try:
        al = list_file.read().splitlines()
        print('Lade Geschäfte...')
        list_file.close()
    except Exception as e:
        print('Konnte Datei nicht öffnen. ' + str(e))
        return False

    for affair in al:
        if r1.match(affair):
            s = affair.split('.')
            if len(s[1]) == 3:
                aid = '20' + s[0] + '0' + s[1]
            else:
                aid = '20' + s[0] + s[1]
            affairs_list.append(aid)
        elif r2.match(affair):
            affairs_list.append(affair)
        else:
            print('[!] Ungültiger Eintrag: ' + affair)

    print(str(len(affairs_list)) + ' Geschäfte geladen.')
    return affairs_list


# Hole JSON-Daten via API oder Cache
def get_json(affairid):
    global api_url, lang

    if args.from_cache:
        try:
            f = open('cache/' + affairid + '.txt', 'r')
            raw_data = f.read()
        except FileNotFoundError:
            print('[!] Cache für ' + affairid + ' existiert nicht. Verwende --create-cache um Cache zu erstellen.')
            return False
        except Exception as e:
            print('[!] Fehler beim Öffnen des Caches für ' + affairid + '. ' + str(e))
            return False
    else:
        try:
            url = api_url + 'affairs/' + affairid + '?format=json&lang=' + lang
            headers = {'Accept': 'text/json'}
            r = requests.get(url, headers=headers)
        except Exception as e:
            print('[!] Verbindungsfehler. ' + str(e))
            return False

        if r.status_code == 200:
            raw_data = r.text
            # Caching
            if args.create_cache:
                create_cache(affairid, raw_data)
        else:
            print('[!] ' + affairid + ': Konnte Geschäftsdaten nicht abrufen. Ungültige Geschäftsnummer?')
            return False

    return json.loads(raw_data)


# Cache JSON-Rohdaten
def create_cache(affairid, raw_data):
    try:
        f = open('cache/' + affairid + '.txt', 'w')
        f.write(raw_data)
        f.close()
    except Exception as e:
        print('[!] Konnte Cache für ' + affairid + ' nicht schreiben. ' + str(e))
    return


# Vergleiche Datum
def check_recent_update(updated, delta):
    global today
    dt = datetime.fromisoformat(updated[:-1])
    td = today - dt

    if td.days <= delta:
        return True
    else:
        return False


# Start Main
def main():
    # Lade Geschäfte
    affairs = load_affairs(args.listfile)
    print()

    # Cache-Ordner
    if args.create_cache:
        foldername = 'cache'
        if not os.path.exists(foldername):
            try:
                os.makedirs(foldername)
            except Exception as e:
                print('[!] Konnte Order cache nicht erstellen. ' + str(e))
                args.create_cache = False

    # Ende falls --dry
    if args.dry:
        print("[i] Dry-Run: Geschäfte werden nicht gegen Datenbank geprüft.")
        return

    # Prüfe Daten
    i = 0
    for affair in affairs:
        affair_data = get_json(affair)
        if affair_data:
            # Prüfe Aktualisierungsdatum
            if check_recent_update(affair_data['updated'], args.t):
                print(affair_data['shortId'] + ': ' + affair_data['title']
                      + ' (' + affair_data['updated'][0:10] + ')')
                i += 1
            else:
                # Information, falls Geschäft bereits erledigt ist
                if affair_data['state']['doneKey'] == '1' and not args.ignore_done:
                    print('[i] Erledigtes Geschäft: ' + affair_data['shortId'] + ': ' + affair_data['title'])

    print()
    print(str(i) + ' Geschäfte gefunden, die in den letzten ' + str(args.t) + ' Tagen aktualisiert wurden.')
    return


if __name__ == '__main__':
    main()
