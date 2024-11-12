import json
from datetime import datetime, timedelta

class WeatherFileHandler:
    """handles operations with file"""

    def read_file(self, file_path: 'path')-> 'tuple':
        """loads data from json"""
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data

    def weather_location(self, data: 'tuple')-> None:
        """calculates and prints avg weather location"""
        coordinates = data['geometry']['coordinates'][0]
        avg_latitude = sum(point[1] for point in coordinates) / len(coordinates)
        avg_longitude = sum(point[0] for point in coordinates) / len(coordinates)
        lat_hemisphere = "N" if avg_latitude > 0 else "S"
        lon_hemisphere = "W" if avg_longitude < 0 else "E"
        print(f"FORECAST {abs(avg_latitude)}°{lat_hemisphere} {abs(avg_longitude)}°{lon_hemisphere}")

    def process_temperature(self, data: 'tuple', scale: str, hours: int, limit: str)-> None:
        '''process temp'''
        end_time = datetime.utcnow() + timedelta(hours=hours)
        temperatures = [
            period['temperature'] for period in data['properties']['periods']
            if datetime.fromisoformat(period['startTime'][:-6]) <= end_time
        ]

        if scale == 'C':
            temperatures = [(temp - 32) * 5.0 / 9.0 for temp in temperatures]

        result = max(temperatures) if limit == 'MAX' else min(temperatures)
        forecast_time = data['properties']['periods'][0]['startTime']
        print(f"{forecast_time} {result:.4f}")

    def process_humidity(self, data: 'tuple', hours: int, limit: str)-> None:
        '''processing humidity'''
        end_time = datetime.utcnow() + timedelta(hours=hours)
        humidity_values = [
            (period['startTime'], period['relativeHumidity']['value'])
            for period in data['properties']['periods']
            if datetime.fromisoformat(period['startTime'][:-6]) <= end_time
        ]
        
        if not humidity_values:
            print("No humidity data available within the specified time range.")
            return

        if limit == 'MAX':
            selected_time, selected_value = max(humidity_values, key=lambda x: x[1])
        else:
            selected_time, selected_value = min(humidity_values, key=lambda x: x[1])

        print(f"{selected_time} {selected_value:.4f}%")


    def process_wind(self, data: 'tuple', hours: int, limit: str)-> None:
        '''processing wind speed'''
        end_time = datetime.utcnow() + timedelta(hours=hours)
        wind_speeds = [
            (period['startTime'], int(period['windSpeed'].split()[0]))
            for period in data['properties']['periods']
            if datetime.fromisoformat(period['startTime'][:-6]) <= end_time
        ]
        
        if not wind_speeds:
            print("No wind data available within the specified time range.")
            return

        if limit == 'MAX':
            selected_time, selected_value = max(wind_speeds, key=lambda x: x[1])
        else:
            selected_time, selected_value = min(wind_speeds, key=lambda x: x[1])

        print(f"{selected_time} {selected_value:.4f}")


    def process_precipitation(self, data: 'tuple', hours: int, limit: str)-> None:
        '''processing precipitation percent'''
        end_time = datetime.utcnow() + timedelta(hours=hours)
        precipitation_values = [
            (period['startTime'], period['probabilityOfPrecipitation']['value'])
            for period in data['properties']['periods']
            if datetime.fromisoformat(period['startTime'][:-6]) <= end_time and period['probabilityOfPrecipitation']['value'] is not None
        ]
        
        if not precipitation_values:
            print("No precipitation data available within the specified time range.")
            return
        
        if limit == 'MAX':
            selected_time, selected_value = max(precipitation_values, key=lambda x: x[1])
        else:
            selected_time, selected_value = min(precipitation_values, key=lambda x: x[1])

        print(f"{selected_time} {selected_value:.4f}%")


    def process_feels_like(self, data: 'tuple', scale: str, hours: int, limit: str)-> None:
        '''calcualtes based off formula feels like temp'''
        end_time = datetime.utcnow() + timedelta(hours=hours)
        feels_like_values = []

        for period in data['properties']['periods']:
            start_time = period['startTime']
            temp_f = period['temperature']
            humidity = period['relativeHumidity']['value']
            wind_speed = int(period['windSpeed'].split()[0])

            if datetime.fromisoformat(start_time[:-6]) > end_time:
                continue

            if temp_f >= 68:  
                feels_like = (
                    -42.379 +
                    2.04901523 * temp_f +
                    10.14333127 * humidity -
                    0.22475541 * temp_f * humidity -
                    0.00683783 * (temp_f ** 2) -
                    0.05481717 * (humidity ** 2) +
                    0.00122874 * (temp_f ** 2) * humidity +
                    0.00085282 * temp_f * (humidity ** 2) -
                    0.00000199 * (temp_f ** 2) * (humidity ** 2)
                )
            elif temp_f <= 50 and wind_speed > 3:  
                feels_like = (
                    35.74 +
                    0.6215 * temp_f -
                    35.75 * (wind_speed ** 0.16) +
                    0.4275 * temp_f * (wind_speed ** 0.16)
                )
            else:  
                feels_like = temp_f

            if scale == 'C':
                feels_like = (feels_like - 32) * 5.0 / 9.0

            feels_like_values.append((start_time, round(feels_like, 4)))

        if feels_like_values:
            selected_time, selected_value = max(feels_like_values, key=lambda x: x[1]) if limit == 'MAX' else min(feels_like_values, key=lambda x: x[1])
            print(f"{selected_time} {selected_value:.4f}")
        else:
            print("No feels like temperature data available within the specified time range.")

from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json
import time

class WeatherAPIHandler:
    """hands notional weather service api"""

    BASE_URL = "https://api.weather.gov/"
    USER_AGENT = "(https://www.ics.uci.edu/~thornton/icsh32/ProjectGuide/Project3/, anthopn5@uci.edu)"

    def __init__(self):
        self.last_url = None

    def fetch_weather_data(self, latitude: float, longitude:float)-> 'tuple':
        """fetches hoursley weather forecast"""
        
        points_endpoint = f"points/{latitude},{longitude}"
        self.last_url = self.BASE_URL + points_endpoint
        request = Request(self.last_url)
        request.add_header("User-Agent", self.USER_AGENT)

        try:
            with urlopen(request) as response:
                if response.status != 200:
                    raise HTTPError(self.last_url, response.status, "Status not 200", None, None)
                data = json.load(response)
                forecast_url = data['properties']['forecastHourly']
                
                return self._fetch_hourly_forecast(forecast_url)
                
        except HTTPError as e:
            print(f"HTTP Error: {e.code} for URL: {self.last_url}")
        except URLError as e:
            print(f"Error accessing National Weather Service API: {e}")
            return None

    def _fetch_hourly_forecast(self, forecast_url: str)-> 'tuple':
        """Fetches the hourly forecast data from the provided forecast URL."""
        self.last_url = forecast_url
        request = Request(forecast_url)
        request.add_header("User-Agent", self.USER_AGENT)

        try:
            with urlopen(request) as response:
                if response.status != 200:
                    raise HTTPError(self.last_url, response.status, "Status not 200", None, None)
                data = json.load(response)
                coordinates = data['geometry']['coordinates'][0]
                unique_coords = {tuple(coord) for coord in coordinates}
                avg_latitude = sum(coord[1] for coord in unique_coords) / len(unique_coords)
                avg_longitude = sum(coord[0] for coord in unique_coords) / len(unique_coords)
                
                time.sleep(1) 
                return data, (avg_latitude, avg_longitude)
        except HTTPError as e:
            print(f"HTTP Error: {e.code} for URL: {self.last_url}")
        except URLError as e:
            print(f"Error accessing National Weather Service API: {e}")
            return None
