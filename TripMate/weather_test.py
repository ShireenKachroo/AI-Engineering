# Independent API TESTING

import requests

# GET city coordinates
city_name = input("Enter the city you want to visit: ").strip()
geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
geocoding_params = {
	"name": city_name,
	"count": 1,
	"language": "en",
	"format": "json"
}

try:
	response = requests.get(geocoding_url, params=geocoding_params, timeout = 10)

	response.raise_for_status()
	data  = response.json()

	if "results" not in data:
		print(f"No location found for '{city_name}'. Please check the city name and try again.")
	else:
		location = data["results"][0]
		latitude = location["latitude"]
		longitude = location["longitude"]
		print(f"Coordinates for {city_name}: Latitude {latitude}, Longitude {longitude}")

except requests.exceptions.Timeout:
	print("Request timed out. Please try again.")

except requests.exceptions.RequestException as e:
	print(f"API request failed: {e}")


# GET WEATHER FORECAST
weather_url = "https://api.open-meteo.com/v1/forecast"
weather_params = {
	"latitude": latitude,
	"longitude": longitude,
	"daily": [
		"weather_code",
		"temperature_2m_max",
		"temperature_2m_min",
		"precipitation_probability_max"
	],
	"timezone": "auto",
	"forecast_days": 3
}

try:
	weather_response = requests.get(weather_url, params=weather_params, timeout = 10)
	weather_response.raise_for_status()
	weather_data = weather_response.json()
	daily = weather_data["daily"]
	print("\n3-Day Weather Forecast:\n")
	for i in range(len(daily["time"])):
		date = daily["time"][i]
		weather_code = daily["weather_code"][i]
		temp_max = daily["temperature_2m_max"][i]
		temp_min = daily["temperature_2m_min"][i]
		precip_prob = daily["precipitation_probability_max"][i]

		print(f"Date: {date}")
		print(f"Weather Code: {weather_code}")
		print(f"Max Temperature: {temp_max}°C")
		print(f"Min Temperature: {temp_min}°C")
		print(f"Rain Probability: {precip_prob}%\n")

except requests.exceptions.Timeout:
	print("Weather request timed out. Please try again.")

except (KeyError, IndexError, TypeError) as e:
	print(f"Error processing weather data: {e}")

except requests.exceptions.RequestException as e:
	print(f"Weather API request failed: {e}")