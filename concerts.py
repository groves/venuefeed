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
            resp = self._get('venues/%s/calendar.json' % venueId, page=page, per_page=perPage)
            resultsPage = resp.json()["resultsPage"]
            if 'event' in resultsPage['results']:
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
        self.date = eventjson["start"]["date"]
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

    def _mergeeventiddicts(self, mergeinto, mergefrom, lognew):
        for eventid, event in mergeinto.items():
            if eventid in mergefrom and mergefrom[eventid].displayname == event.displayname:
                mergeinto[eventid] = mergefrom[eventid]
            elif lognew:
                print "Not previously seen", event

    def merge(self, other):
        for venue, otherevents in other.byvenue.iteritems():
            if venue not in self.byvenue:
                continue
            self._mergeeventiddicts(self.byvenue[venue], otherevents, lognew=True)
        self._mergeeventiddicts(self.byeventid, other.byeventid, lognew=False)

    def _writefeed(self, title, events):
        fn = title.replace(" ", "_") + ".atom"
        feed = atom.AtomFeed(title, url="%s%s" % (config.urlbase, fn))
        # Include the events by the day we last saw an update and then the day of the event inside of that
        for event in sorted(events, key=lambda e: e.updated.date().isoformat() + e.date):
            feed.add(event.displayname, url=event.uri, updated=event.updated)
        open('feeds/%s' % fn, 'w').write(feed.to_string().encode('utf-8'))

    def writefeeds(self):
        self._writefeed("All Concerts", self.byeventid.values())
        for venueid, events in self.byvenue.iteritems():
            self._writefeed(config.venues[venueid], events.values())

# Touch all of our config stuff just to make sure it's defined
print "Fetching %s venues to be hosted at %s" % (len(config.venues), config.urlbase)
client = SongkickClient(config.apikey)

existing = Cache()
if os.path.exists("concerts.pickle"):
    existing = pickle.load(open('concerts.pickle', 'rb'))


fetched = Cache()
for venueid, venue in config.venues.iteritems():
    print "Fetching", venue
    upcoming = client.fetchVenueCalendar(venueid)
    for u in upcoming:
        fetched.add(venueid, Event(u))

fetched.merge(existing)
fetched.writefeeds()
pickle.dump(fetched, open('concerts.pickle', 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
