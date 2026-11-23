import requests

city_name = input("Enter the city you want to visit: ").strip()
url = "https://geocoding-api.open-meteo.com/v1/search"
params = {
	"name": city_name,
	"count": 5,
	"language": "en",
	"format": "json"
}

try:
	response = requests.get(url, params=params, timeout = 10)
	response.raise_for_status()

	data  = response.json()

	if "results" not in data:
		print(f"No location found for '{city_name}'. Please check the city name and try again.")
	else:
		print("\nLocations Found:: \n")
		for location in data["results"]:
			print(f"City: {location['name']}, Country: {location['country']}, Latitude: {location['latitude']}, Longitude: {location['longitude']}")

except requests.exceptions.Timeout:
	print("Request timed out. Please try again.")

except requests.exceptions.RequestException as e:
	print(f"API request failed: {e}")