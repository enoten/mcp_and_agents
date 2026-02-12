from googlemaps import Client as GoogleMaps
import json
import os
from dotenv import load_dotenv
load_dotenv()


# Replace with your actual API key
#YOUR_API_KEY = 'YOUR_API_KEY'
gmaps = GoogleMaps(os.environ['GOOGLE_MAPS_API_KEY'])

# The city name you want to geocode
city_name = "New York City"

# Geocoding the city name
geocode_result = gmaps.geocode(city_name)

if geocode_result:
    # Extracting latitude and longitude
    location = geocode_result[0]['geometry']['location']
    latitude = location['lat']
    longitude = location['lng']
    print(f"City: {city_name}")
    print(f"Latitude: {latitude}")
    print(f"Longitude: {longitude}")
else:
    print(f"Geocoding failed for {city_name}")