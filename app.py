import os
import requests

from pprint import PrettyPrinter
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file
from geopy.geocoders import Nominatim


################################################################################
## SETUP
################################################################################

app = Flask(__name__)

# Get the API key from the '.env' file
load_dotenv()

pp = PrettyPrinter(indent=4)

API_KEY = os.getenv('API_KEY')
API_URL = 'http://api.openweathermap.org/data/2.5/weather'


################################################################################
## ROUTES
################################################################################

@app.route('/')
def home():
    """Displays the homepage with forms for current or historical data."""
    context = {
        'min_date': (datetime.now() - timedelta(days=5)),
        'max_date': datetime.now()
    }
    return render_template('home.html', **context)

def get_letter_for_units(units):
    """Returns a shorthand letter for the given units."""
    return 'F' if units == 'imperial' else 'C' if units == 'metric' else 'K'

@app.route('/results')
def results():
    """Displays results for current weather conditions."""
    # Retrieve the city and units from the query parameters
    city = request.args.get('city', '')  # Default to empty string if not found
    units = request.args.get('units', 'imperial')  # Default to 'imperial' if not found

    # Set up the API parameters
    params = {
        'q': city,
        'appid': API_KEY,  # API key from the .env file
        'units': units
    }

    
    result_json = requests.get(API_URL, params=params).json()

    
    if result_json.get('cod') != 200:
        
        return render_template('error.html', message="City not found or API error.")

    
    city_name = result_json['name']
    description = result_json['weather'][0]['description']
    temp = result_json['main']['temp']
    humidity = result_json['main']['humidity']
    wind_speed = result_json['wind']['speed']
    
    
    sunrise = datetime.fromtimestamp(result_json['sys']['sunrise'])
    sunset = datetime.fromtimestamp(result_json['sys']['sunset'])

    
    context = {
        'date': datetime.now(),
        'city': city_name,
        'description': description,
        'temp': temp,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'sunrise': sunrise,
        'sunset': sunset,
        'units_letter': get_letter_for_units(units)
    }

    return render_template('results.html', **context)



@app.route('/comparison_results')
def comparison_results():
    """Displays the relative weather for 2 different cities."""
    city1 = request.args.get('city1')
    city2 = request.args.get('city2')
    units = request.args.get('units')

    # Function to make API call and get data for a city
    def get_weather_data(city):
        params = {
            'q': city,
            'appid': API_KEY,
            'units': units
        }
        response = requests.get(API_URL, params=params).json()
        return {
            'city': city,
            'temp': response['main']['temp'],
            'description': response['weather'][0]['description'],
            'humidity': response['main']['humidity'],
            'wind_speed': response['wind']['speed'],
            'sunset': datetime.fromtimestamp(response['sys']['sunset']),
            'temp_min': response['main']['temp_min'],
            'temp_max': response['main']['temp_max']
        }

    # Get weather data for both cities
    city1_info = get_weather_data(city1)
    city2_info = get_weather_data(city2)

    # Calculate differences and comparisons
    temp_diff = abs(city1_info['temp'] - city2_info['temp'])
    temp_comparison = 'warmer' if city1_info['temp'] > city2_info['temp'] else 'colder'

    humidity_diff = abs(city1_info['humidity'] - city2_info['humidity'])
    humidity_comparison = 'greater' if city1_info['humidity'] > city2_info['humidity'] else 'less'

    wind_speed_diff = abs(city1_info['wind_speed'] - city2_info['wind_speed'])
    wind_speed_comparison = 'greater' if city1_info['wind_speed'] > city2_info['wind_speed'] else 'less'

    sunset_diff = abs((city1_info['sunset'] - city2_info['sunset']).total_seconds()) / 3600  # in hours
    sunset_comparison = 'earlier' if city1_info['sunset'] < city2_info['sunset'] else 'later'

    # Pass the data to the template
    context = {
        'city1_info': city1_info,
        'city2_info': city2_info,
        'date': datetime.now(),  
        'temp_diff': temp_diff,
        'temp_comparison': temp_comparison,
        'humidity_diff': humidity_diff,
        'humidity_comparison': humidity_comparison,
        'wind_speed_diff': wind_speed_diff,
        'wind_speed_comparison': wind_speed_comparison,
        'sunset_diff': sunset_diff,
        'sunset_comparison': sunset_comparison,
        'units_letter': get_letter_for_units(units)
    }

    return render_template('comparison_results.html', **context)




if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True, port=5001)


