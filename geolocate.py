
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def find_nearest_clinic(region_query='Hyderabad, India'):
    try:
        geolocator = Nominatim(user_agent='symptom_checker_app')
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        base = geocode(region_query)
        if not base:
            return None
        lat, lon = base.latitude, base.longitude
        # Search for 'clinic' nearby via Nominatim reverse search (note: limited and approximate)
        # We'll perform a nearby search by querying 'clinic' with city name
        query = f'clinic near {region_query}'
        results = geolocator.geocode(query, exactly_one=False, limit=5)
        if not results:
            return None
        first = results[0]
        return {'name': first.address.split(',')[0], 'address': first.address}
    except Exception as e:
        print('Clinic lookup failed:', e)
        return None
