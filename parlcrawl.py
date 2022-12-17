#!/bin/python3

# Module
import argparse
import json
import os
import re
import requests

from datetime import datetime
from progress.bar import Bar
from termcolor import colored

# Globale Variablen
api_url = 'http://ws-old.parlament.ch/'
cacheFolder = 'cache'
lang = 'de'
r1 = re.compile(r'\d{2}\.\d{3,4}')  # Format für Geschäftsnummern
r2 = re.compile(r'\d{8}')  # Format für Geschäfts-IDs
today = datetime.today()
version = '1.61'

# ArgumentParser
ap = argparse.ArgumentParser(usage='%(prog)s [-h] [-t Zeitraum] Geschäfts-Liste',
                             description='Parlcrawl v' + version,
                             epilog='\b')

ap.add_argument('listfile', type=argparse.FileType('r'), metavar='Geschäftsliste',
                help='Text-Datei mit Geschäftsnummern (eine pro Zeile) als ID (20212355) oder Kurzform (21.2355).')
ap.add_argument('--compare', type=argparse.FileType('r'), metavar='Vergleichsliste',
                help='Text-Datei mit Geschäftsnummern (eine pro Zeile) als ID (20212355) oder Kurzform (21.2355).')
ap.add_argument('--create-cache', action='store_true',
                help='Speichert die abgerufenen Daten lokal ab.')
ap.add_argument('--dry', action='store_true',
                help='Prüft nur die Dateiliste ohne Anfrage an die API.')
ap.add_argument('--from-cache', action='store_true',
                help='Liest Geschäftsdaten aus dem Cache anstelle der API.')
ap.add_argument('--ignore-done', action='store_true',
                help='Blendet Information aus, wenn Geschäfte erledigt sind.')
ap.add_argument('--print-state', action='store_true',
                help='Zeigt den letzten Status (Bei Geschäften mit mehreren Entwürfen: nur Entwurf 1).')
ap.add_argument('-t', type=int, default=7, metavar='Tage',
                help='Zeitraum, für den geänderte Vorstösse angezeigt werden (Standard: 7).')
args = ap.parse_args()


# Lade Geschäftsliste
def load_affairs(list_file):
    global r1, r2
    affairs_list = []
    al = []

    try:
        al = list_file.read().splitlines()
    except Exception as e:
        print(colored('[!] Konnte Datei nicht öffnen. ' + str(e), 'red'))
    else:
        list_file.close()

    for affair in al:
        if r1.match(affair):
            s = affair.split('.')
            if len(s[1]) == 3:
                aid = '20' + s[0] + '0' + s[1]
            else:
                aid = '20' + s[0] + s[1]
            append = aid
        elif r2.match(affair):
            append = affair
        else:
            print(colored('[!] Ungültiger Eintrag: ' + affair, 'red'))
            continue

        # Check auf Duplikate
        if append in affairs_list:
            print(colored('[!] Duplikat: ' + append, 'magenta'))
        else:
            affairs_list.append(append)

    return affairs_list


# Hole JSON-Daten via API oder Cache
def get_json(affairid):
    global api_url, lang

    if args.from_cache:
        try:
            raw_data = from_cache(affairid)
        except Exception as e:
            raise Exception(str(e))
    else:
        url = api_url + 'affairs/' + affairid + '?format=json&lang=' + lang
        headers = {'Accept': 'text/json'}

        try:
            r = requests.get(url, headers=headers)
        except Exception as e:
            raise Exception('Verbindungsfehler. ' + str(e))
        else:
            if r.status_code == 200:
                raw_data = r.text
                # Caching
                if args.create_cache:
                    try:
                        create_cache(affairid, raw_data)
                    except Exception as e:
                        raise Exception(str(e))
            else:
                raise Exception(affairid + ': Konnte Geschäftsdaten nicht abrufen. Ungültige Geschäftsnummer?')

    return json.loads(raw_data)


# Prüfe / Erstelle Cache-Ordner
def check_cache_folder(folder_name):
    if os.path.exists(folder_name):
        return True
    else:
        try:
            os.makedirs(folder_name)
        except Exception as e:
            print(colored('[!] Konnte Order cache nicht erstellen. ' + str(e), 'red'))
        else:
            return True
    return False


# Cache JSON-Rohdaten
def create_cache(affairid, raw_data):
    global cacheFolder
    if not check_cache_folder(cacheFolder):
        return

    try:
        f = open(cacheFolder + '/' + affairid + '.txt', 'w')
    except Exception as e:
        raise Exception('Konnte Cache für ' + affairid + ' nicht schreiben. ' + str(e))

    f.write(raw_data)
    f.close()
    return


# Hole Daten aus Cache
def from_cache(affairid):
    global cacheFolder
    raw_data = ''

    if check_cache_folder(cacheFolder):
        try:
            f = open(cacheFolder + '/' + affairid + '.txt', 'r')
        except FileNotFoundError:
            raise Exception('Cache für ' + affairid +
                            ' existiert nicht. Verwende --create-cache um Cache zu erstellen.')
        except Exception as e:
            raise Exception('Konnte Cache nicht öffnen für ' + affairid + '. ' + str(e))
        else:
            raw_data = f.read()

    return raw_data


# Vergleiche Datum
def check_recent_update(updated, delta):
    global today
    dt = datetime.fromisoformat(updated[:-1])
    td = today - dt

    return td.days <= delta


# Geschäfts-Status auslesen
def get_state(affair_data):
    # TODO: Angepasste Informationen je nach Geschäftstyp
    if len(affair_data['drafts'][0]['consultation']['resolutions']) > 0:
        state = affair_data['drafts'][0]['consultation']['resolutions'][-1]['text'] \
                + ' (' + affair_data['drafts'][0]['consultation']['resolutions'][-1]['date'][0:10] + ')'
    else:
        state = 'Kein Status'

    return state


# Start Main
def main():
    # Lade Geschäfte
    print(colored('### Lade Geschäfte...', 'yellow'))
    affairs = load_affairs(args.listfile)
    print(str(len(affairs)) + ' Geschäfte geladen.\n')

    # Falls Vergleichsliste angegeben
    if args.compare:
        print(colored('### Vergleiche Geschäftsliste mit Vergleichsliste...', 'yellow'))
        i = 0
        compare_list = load_affairs(args.compare)
        for compare_item in compare_list:
            if compare_item in affairs:
                print(colored(compare_item, 'cyan') + ' ist in Vergleichsliste enthalten.')
                i += 1
        print('\n' + colored(str(i) + ' Geschäft(e) in Vergleichsliste gefunden.\n'
                                      '### Vergleich abgeschlossen\n', 'yellow'))

    # Ende falls --dry
    if args.dry:
        print(colored('[i] Dry-Run: Geschäfte werden nicht gegen Datenbank geprüft.', 'magenta'))
        return

    # Prüfe Daten
    print(colored('### Prüfe Geschäftsliste auf aktualisierte Geschäfte...', 'yellow'))
    bar = Bar('Bitte warten...', max=len(affairs))
    updated_affairs = []
    affairs_done = []

    for affair in affairs:
        try:
            affair_data = get_json(affair)
        except Exception as e:
            print(colored('[!] ' + str(e), 'red'))
            bar.next()
            continue

        # Prüfe Aktualisierungsdatum
        if check_recent_update(affair_data['updated'], args.t):
            updated_affairs.append({'shortId': affair_data['shortId'],
                                    'title': affair_data['title'],
                                    'updated': affair_data['updated'][0:10],
                                    'state': get_state(affair_data)})
        else:
            # Erledigte Geschäfte
            if affair_data['state']['doneKey'] == '1':
                affairs_done.append({'shortId': affair_data['shortId'],
                                     'title': affair_data['title']})

        bar.next()
    bar.finish()

    # Sortiere Geschäfte nach Datum
    updated_affairs = sorted(updated_affairs, key=lambda x: x['updated'])

    # Zeige aktualisierte Geschäfte
    print('\n' + colored(str(len(updated_affairs)) + ' Geschäft(e) gefunden mit Aktualisierungsdatum in den letzten ' +
                         str(args.t) + ' Tagen', 'yellow'))
    for affair in updated_affairs:
        p = colored(affair['shortId'] + ': ', 'cyan') + affair['title'] + ' (' + affair['updated'][0:10] + ')'

        # Geschäftsstatus
        if args.print_state:
            p += colored(' ' + affair['state'] , 'magenta')

        print(p)

    # Zeige erledigte Geschäfte
    if len(affairs_done) > 0 and not args.ignore_done:
        print(colored('\n[i] ' + str(len(affairs_done)) + ' erledigte Geschäfte', 'yellow'))

        for affair in affairs_done:
            print(colored(affair['shortId'] + ': ', 'cyan') +
                  affair['title'])

    print('')
    return


if __name__ == '__main__':
    main()
