import requests
from googlemaps import Client as GoogleMaps
import os
from dotenv import load_dotenv
load_dotenv()

def get_city_lat_long(city_name: str) -> str:
    gmaps = GoogleMaps(os.environ['GOOGLE_MAPS_API_KEY'])
    # The city name you want to geocode
    # Geocoding the city name
    geocode_result = gmaps.geocode(city_name)
    if geocode_result:
        # Extracting latitude and longitude
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        print(f"Geocoding failed for {city_name}")
        return None


def get_current_weather(city_name):
    # 1. Get Coordinates
    #lat, lon = get_coordinates(city_name)
    lat, lon = get_city_lat_long(city_name)
    
    if not lat:
        print(f"Error: Could not find coordinates for '{city_name}'.")
        return

    # 2. Setup NWS API Request
    # NWS requires a User-Agent header with contact info (email or app name)
    headers = {
        "User-Agent": "(my_weather_script, my_email@example.com)",
        "Accept": "application/geo+json"
    }

    # 3. Get Grid Point Data (The "Handshake")
    # The NWS API doesn't take lat/lon for weather directly. 
    # It takes lat/lon to give you a "grid point" URL.
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    
    try:
        response = requests.get(points_url, headers=headers)
        response.raise_for_status()
        points_data = response.json()
        
        # Extract the hourly forecast URL from the response
        forecast_hourly_url = points_data['properties']['forecastHourly']

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to NWS API: {e}")
        return
    except KeyError:
        print("Error: Location is likely outside the US (NWS only covers US territories).")
        return

    # 4. Get the Actual Forecast
    try:
        forecast_response = requests.get(forecast_hourly_url, headers=headers)
        forecast_response.raise_for_status()
        weather_data = forecast_response.json()
        
        # Get the first period (current hour)
        current_period = weather_data['properties']['periods'][0]
        
        print(f"--- Current Weather in {city_name} ---")
        print(f"Temperature: {current_period['temperature']}°{current_period['temperatureUnit']}")
        print(f"Condition:   {current_period['shortForecast']}")
        print(f"Wind:        {current_period['windSpeed']} {current_period['windDirection']}")
        print(f"Forecast:    {current_period['detailedForecast']}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast: {e}")

# Example Usage
if __name__ == "__main__":
    city = input("Enter city (e.g., 'San Francisco, CA'): ")
    get_current_weather(city)