# ParlCrawl

Monitoring-Tool für Geschäfte des Schweizerischen Parlaments. ParlCrawl prüft anhand einer Liste mit relevanten parlamentarischen Geschäften, welche dieser Geschäfte kürzlich aktualisiert wurden. Die Abfrage erfolgt über die [offizielle API](http://ws-old.parlament.ch/) des Parlaments.

## Installation
```
$ pip install -r requirements.txt
```

## Verwendung
```
$ python parlcrawl.py geschaeftsliste.txt
```

Die Geschäftsliste ist ein Textdokument mit einer Geschäftsnummer pro Zeile. Die Geschäftsnummer kann im Curia-Vista-Format (20221348) oder in Kurzform (22.1348) angegeben werden.

### Beispielformat Geschäftsliste
```
21.4077
21.4095
21.4115
```

## Einstellungen
### Zeitraum anpassen
Standardmässig listet ParlCrawl alle Geschäfte, die in den vergangenen 7 Tagen aktualisiert wurden. Der Zeitraum kann mit dem Argument -t angepasst werden (Anzahl Tage).

```
$ python parlcrawl.py -t 30 geschaeftsliste.txt
```

### Caching
ParlCrawl kann die abgefragten Geschäftsinfos zwischenspeichern.
```
$ python parlcrawl.py --create-cache geschaeftsliste.txt
```
Die zwischengespeicherten Daten können in einer nächsten Anfrage verwendet werden (z. B. um verschiedene Parameter für den Zeitraum auszuprobieren). Bei der Verwendung von --from-cache werden keine Anfragen an die API getätigt. Nicht gecachte Geschäftsnummern werden ignoriert.
```
$ python parlcrawl.py --from-cache geschaeftsliste.txt
```

### Weitere Optionen
```
--compare vergleichsliste.txt
```
Prüft, ob Geschäfte in der Geschäftsliste in einer Vergleichsliste vorkommen.
```
--dry
```
Liest nur die Geschäftsliste in den Speicher, ohne Anfragen an die API (oder den Cache) durchzuführen. Diese Option kann genutzt werden, um zu prüfen, ob die Geschäftsliste fehlerhafte oder doppelte Einträge enthält.
```
--ignore-done
```
Standardmässig meldet ParlCrawl, wenn ein Geschäft in der Geschäftsliste bereits als erledigt gekennzeichnet ist. Dieses Argument deaktiviert diese Hinweise.
```
--print-state
```
Gibt den letzten Status eines Geschäfts gemäss API aus. Bei Geschäften mit mehreren Teilen (Entwürfen) wird nur der Status des ersten Teils ausgegeben.

### Hilfe
```
$ python parlcrawl.py -h
```
