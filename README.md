Fetches concerts by venue from Songkick and makes atom feeds out of them.

To use, create a `config.py` like:

```python
apikey = 'MY API KEY'
venues = {'songkick venue id': 'Venue Name for Feed',
          'another venue id': 'Another Venue Name'}
urlbase = 'http://blah.myhost.com/'
```

A sample configuration file can be found in the `examples` directory.

Install `requests` from PyPI, and run `python concerts.py` periodically.

Thanks, Songkick!
