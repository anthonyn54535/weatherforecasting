import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

class GeocodingFileHandler:
    """handles locating for files"""

    def read_file(self, geo_file: 'path')-> 'tuple':
        """returns data of json"""
        with open(geo_file, 'r') as file:
            data = json.load(file)
        return data

    def location(self, data: 'tupl')-> None:
        """prints lat and long"""
        latitude = float(data[0]['lat'])
        longitude = float(data[0]['lon'])
        lat_hemisphere = "N" if latitude > 0 else "S"
        lon_hemisphere = "W" if longitude < 0 else "E"
        print(f"TARGET {abs(latitude)}/{lat_hemisphere} {abs(longitude)}/{lon_hemisphere}")

    def reverse_location(self, data: 'tuple')-> None:
        """Prints address from reverse geocoded data."""
        address = data.get('display_name', 'Address Not Found')
        print(address)

class NominatimAPIHandler:
    """Handles interactions with the Nominatim API for geocoding."""

    BASE_URL = "https://nominatim.openstreetmap.org/"
    REFERER_URL = "https://www.ics.uci.edu/~thornton/icsh32/ProjectGuide/Project3/anthopn5" 

    def __init__(self):
        self.last_url = None  

    def forward_geocode(self, location: str)-> float:
        """performs geocoding"""
        params = {
            'q': location,
            'format': 'jsonv2'
        }
        self.last_url = self.BASE_URL + "search?" + urlencode(params)
        
        request = Request(self.last_url)
        request.add_header("Referer", self.REFERER_URL)

        try:
            with urlopen(request) as response:
                if response.status != 200:
                    raise HTTPError(self.last_url, response.status, "Status not 200", None, None)
                data = json.load(response)
                if data:
                    lat, lon = data[0]['lat'], data[0]['lon']
                    time.sleep(1)  
                    return lat, lon
                else:
                    return None
        except HTTPError as e:
            print(f"HTTP Error: {e.code} for URL: {self.last_url}")
        except URLError as e:
            print(f"Error accessing Nominatim API: {e}")

    def reverse_geocode(self, latitude: float, longitude: float)-> str:
        """performs geocoding to get DESCRIPTION of location"""
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'jsonv2'
        }
        self.last_url = self.BASE_URL + "reverse?" + urlencode(params)
        
        request = Request(self.last_url)
        request.add_header("Referer", self.REFERER_URL)

        try:
            with urlopen(request) as response:
                if response.status != 200:
                    raise HTTPError(self.last_url, response.status, "Status not 200", None, None)
                data = json.load(response)
                address = data.get('display_name', 'Address Not Found')
                time.sleep(1)  
                return address
        except HTTPError as e:
            print(f"HTTP Error: {e.code} for URL: {self.last_url}")
        except URLError as e:
            print(f"Error accessing Nominatim API: {e}")
