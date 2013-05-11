import atom
import collections
import config
import datetime
import os
import requests
import cPickle as pickle

class SongkickClient(object):
    def __init__(self, apiKey):
        self.apiKey = apiKey
        self.session = requests.Session()

    def fetchVenueCalendar(self, venueId):
        page = 1
        totalEntries = 1
        perPage = 50
        events = []
        while (page - 1) * perPage < totalEntries:
            resp = self._get('venues/%s/calendar.json' % venueId,
                             page=page, per_page=perPage)
            resultsPage = resp.json()["resultsPage"]
            events.extend(resultsPage["results"]["event"])
            totalEntries = resultsPage["totalEntries"]
            page += 1
        return events

    def _get(self, endpoint, **params):
        params['apikey'] = self.apiKey
        url = 'http://api.songkick.com/api/3.0/%s' % endpoint
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp

class Event(object):
    def __init__(self, eventjson):
        self.id = eventjson["id"]
        self.uri = eventjson["uri"]
        self.displayname = eventjson["displayName"]
        self.updated = datetime.datetime.now()

    def __str__(self):
        return 'Event(id=%s, displayname=%s)' % (self.id, self.displayname.encode("utf-8"))

class Cache(object):
    def __init__(self):
        self.byvenue = collections.defaultdict(dict)
        self.byeventid = {}

    def add(self, venueId, event):
        self.byvenue[venueId][event.id] = event
        self.byeventid[event.id] = event

    def _mergeeventiddicts(self, mergeinto, mergefrom):
        for eventid, event in mergeinto.items():
            if eventid in mergefrom and mergefrom[eventid].displayname == event.displayname:
                mergeinto[eventid] = mergefrom[eventid]

    def merge(self, other):
        for venue, otherevents in other.byvenue.iteritems():
            if venue not in self.byvenue:
                continue
            self._mergeeventiddicts(self.byvenue[venue], otherevents)
        self._mergeeventiddicts(self.byeventid, other.byeventid)

    def _writefeed(self, title, events):
        fn = title.replace(" ", "_") + ".atom"
        feed = atom.AtomFeed(title, url="http://aztec.bungleton.com/feeds/%s" % fn)
        for event in sorted(events, key=lambda e: e.updated):
            feed.add(event.displayname, url=event.uri, updated=event.updated)
        open('feeds/%s' % fn, 'w').write(feed.to_string().encode('utf-8'))

    def writefeeds(self):
        self._writefeed("All Concerts", self.byeventid.values())
        for venueid, events in self.byvenue.iteritems():
            self._writefeed(config.venues[venueid], events.values())


existing = Cache()
if os.path.exists("concerts.pickle"):
    existing = pickle.load(open('concerts.pickle', 'rb'))

client = SongkickClient(config.apikey)

fetched = Cache()
for venue in config.venues.iterkeys():
    upcoming = client.fetchVenueCalendar(venue)
    print "got", len(upcoming)
    for u in upcoming:
        fetched.add(venue, Event(u))

fetched.merge(existing)
fetched.writefeeds()
pickle.dump(fetched, open('concerts.pickle', 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
