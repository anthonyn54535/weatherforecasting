from geocoding import GeocodingFileHandler, NominatimAPIHandler
from weather import WeatherFileHandler, WeatherAPIHandler
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError  
import sys

def main() -> None:
    '''initalize'''
    file_handler = GeocodingFileHandler()
    api_handler = NominatimAPIHandler()
    weather_file_handler = WeatherFileHandler()
    weather_api_handler = WeatherAPIHandler()

    commands = []
    temperature_commands = []
    humidity_commands = []
    wind_commands = []
    precipitation_commands = []
    feels_like_commands = []
    weather_data = None
    nws_coordinates = None  

    '''detecting api use'''
    used_forward_geocoding = False
    used_reverse_geocoding = False
    used_real_time_weather = False

    while True:
        line = input().strip()
        if line.startswith("REVERSE FILE") or line.startswith("REVERSE NOMINATIM"):
            commands.append(line)
            break
        elif line.startswith("TARGET FILE") or line.startswith("TARGET NOMINATIM"):
            commands.append(line)
        elif line.startswith("WEATHER FILE") or line.startswith("WEATHER NWS"):
            commands.append(line)
        elif line.startswith("TEMPERATURE AIR"):
            temperature_commands.append(line)
        elif line.startswith("TEMPERATURE FEELS"):
            feels_like_commands.append(line)
        elif line.startswith("HUMIDITY"):
            humidity_commands.append(line)
        elif line.startswith("WIND"):
            wind_commands.append(line)
        elif line.startswith("PRECIPITATION"):
            precipitation_commands.append(line)

    def fail_output(reason: str , resource: str , detail=None)-> None:
        print("FAILED")
        print(resource)
        if detail:
            print(detail)
        print(reason)
        sys.exit(1)

    '''proessing reverse commands'''
    for user_input in commands:
        if user_input.startswith('TARGET FILE'):
            path = ' '.join(user_input.split(' ')[2:])
            try:
                data = file_handler.read_file(path)
                if data:  
                    file_handler.location(data)
                    used_forward_geocoding = False
                else:
                    fail_output("FORMAT", path)
            except FileNotFoundError:
                fail_output("MISSING", path)
            except json.JSONDecodeError:
                fail_output("FORMAT", path)

        elif user_input.startswith('WEATHER FILE'):
            path = ' '.join(user_input.split(' ')[2:])
            try:
                weather_data = weather_file_handler.read_file(path)
                if weather_data:  
                    weather_file_handler.weather_location(weather_data)
                    used_real_time_weather = False
                else:
                    fail_output("FORMAT", path)
            except FileNotFoundError:
                fail_output("MISSING", path)
            except json.JSONDecodeError:
                fail_output("FORMAT", path)

        elif user_input.startswith('REVERSE FILE'):
            path = ' '.join(user_input.split(' ')[2:])
            try:
                data = file_handler.read_file(path)
                if data:
                    file_handler.reverse_location(data)
                    used_reverse_geocoding = False
                else:
                    fail_output("FORMAT", path)
            except FileNotFoundError:
                fail_output("MISSING", path)
            except json.JSONDecodeError:
                fail_output("FORMAT", path)
        if user_input.startswith('TARGET NOMINATIM'):
            location = ' '.join(user_input.split(' ')[2:])
            try:
                lat_lon = api_handler.forward_geocode(location)
                if lat_lon:
                    print(f"TARGET {abs(float(lat_lon[0]))}/N {abs(float(lat_lon[1]))}/W")
                    nws_coordinates = lat_lon
                    used_forward_geocoding = True
                else:
                    fail_output("FORMAT", api_handler.last_url)
            except URLError as e:
                fail_output("NETWORK", api_handler.last_url)
            except HTTPError as e:
                if e.code != 200:
                    fail_output("NOT 200", f"{e.code} {api_handler.last_url}")
                else:
                    fail_output("FORMAT", api_handler.last_url)

        elif user_input.startswith('WEATHER NWS'):
            '''uses coordinates from nominatim'''
            if nws_coordinates:
                try:
                    weather_data, forecast_location = weather_api_handler.fetch_weather_data(nws_coordinates[0], nws_coordinates[1])
                    if weather_data:
                        print(f"FORECAST {abs(float(forecast_location[0])):.6f}/N {abs(float(forecast_location[1])):.6f}/W")
                        address = api_handler.reverse_geocode(forecast_location[0], forecast_location[1])
                        if address:
                            print(f"Location: {address}")
                            used_reverse_geocoding = True
                        used_real_time_weather = True
                    else:
                        fail_output("FORMAT", weather_api_handler.last_url)
                except URLError as e:
                    fail_output("NETWORK", weather_api_handler.last_url)
                except HTTPError as e:
                    if e.code != 200:
                        fail_output("NOT 200", f"{e.code} {weather_api_handler.last_url}")
                    else:
                        fail_output("FORMAT", weather_api_handler.last_url)
            else:
                print("Error: No coordinates available from TARGET NOMINATIM for WEATHER NWS.")
                sys.exit(1)

    '''process weather commands'''
    if weather_data:
        for temp_command in temperature_commands:
            _, _, scale, hours, limit = temp_command.split()
            hours = int(hours)
            weather_file_handler.process_temperature(weather_data, scale, hours, limit)

        for feels_like_command in feels_like_commands:
            _, _, scale, hours, limit = feels_like_command.split()
            hours = int(hours)
            weather_file_handler.process_feels_like(weather_data, scale, hours, limit)

        for humidity_command in humidity_commands:
            _, hours, limit = humidity_command.split()
            hours = int(hours)
            weather_file_handler.process_humidity(weather_data, hours, limit)

        for wind_command in wind_commands:
            _, hours, limit = wind_command.split()
            hours = int(hours)
            weather_file_handler.process_wind(weather_data, hours, limit)

        for precipitation_command in precipitation_commands:
            _, hours, limit = precipitation_command.split()
            hours = int(hours)
            weather_file_handler.process_precipitation(weather_data, hours, limit)

    if used_forward_geocoding:
        print("**Forward geocoding data from OpenStreetMap")
    if used_reverse_geocoding:
        print("**Reverse geocoding data from OpenStreetMap")
    if used_real_time_weather:
        print("**Real-time weather data from National Weather Service, United States Department of Commerce")

if __name__ == '__main__':
    main()
