Fetches concerts by venue from Songkick and makes atom feeds out of them.

To use, create a config.py like
    
    apikey = 'MY API KEY'
    venues = {'songkick venue id': 'Venue Name for Feed',
              'another venue id': 'Another Venue Name'}

install requests from PyPI, and run python concerts.py periodically.

Thanks, Songkick!