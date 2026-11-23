# External API Integrations
import requests
import logging


MAX_TOOL_CALLS = 6
tool_calls_used = 0

def reset_tool_call_budget():
	global tool_calls_used
	tool_calls_used = 0

def consume_tool_budget(tool_name: str) -> bool:
	global tool_calls_used
	if tool_calls_used < MAX_TOOL_CALLS:
		tool_calls_used += 1
		logging.info(f"Tool '{tool_name}' called. Total calls used: {tool_calls_used}/{MAX_TOOL_CALLS}")
		return True
	else:
		logging.warning(f"Tool call limit reached. Cannot call '{tool_name}'.")
		return False


logger = logging.getLogger(__name__)

# API endpoints
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]

# city name ---> geographical coordinates
def _geocode_city(city: str) -> dict:
	"""Fetch geographical coordinates for the user-specified city.
	   Args:
	      city: Name of the city.
	   Returns:
	   	   A dictionary containing latitude and longitude.
	"""

	logger.info(f"Fetching geographical coordinates for city: {city}")
	geocoding_params = {
		"name": city,
		"count": 1,
		"language": "en",
		"format": "json"
	}

	response = requests.get(GEOCODING_URL, params=geocoding_params, timeout=10)
	response.raise_for_status()

	data = response.json()
	if "results" not in data:
		raise ValueError(f"No location found for '{city}'. Please check the city name and try again.")

	location = data["results"][0]
	return {
		"city": location["name"],
		"latitude": location["latitude"],
		"longitude": location["longitude"],
		"country": location.get("country", "Unknown"),
	}



# TOOL 1: WEATHER
def get_weather(city_name: str) -> dict:
	"""Fetch a 3-day weather forecast for the user-specified city.
	   Args:
	      city_name: Name of the city.
	   Returns:
	   	   A dictionary containing location and weather information.
	"""
	if not consume_tool_budget("get_weather"):
		return {"error": "Tool call limit reached. Cannot fetch weather information."}

	logger.info(f"Fetching weather forecast for city: {city_name}")

	try:
		location = _geocode_city(city_name)
		params = {
			"latitude": location["latitude"],
			"longitude": location["longitude"],
			"forecast_days": 3,
			"timezone": "auto",
			"daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "windspeed_10m_max"]
		}

		response = requests.get(WEATHER_URL, params=params, timeout=10)

		response.raise_for_status()
		data = response.json()
		daily = data["daily"]

		forecast = []
		for i in range(len(daily["time"])):
			forecast.append({
				"date": daily["time"][i],
				"max_temp": daily["temperature_2m_max"][i],
				"min_temp": daily["temperature_2m_min"][i],
				"precipitation": daily["precipitation_sum"][i],
				"wind_speed": daily["windspeed_10m_max"][i]
			})
			return {
				"location": location,
				"forecast": forecast
			}

	except (requests.RequestException, ValueError, KeyError) as e:
		logger.error(f"Network error while fetching weather data: {e}")
		return {"error": f"Network error while fetching weather data: {e}"}


# PLACES OF INTEREST
def get_places_of_interest(city_name: str, place_type:str, category:str = "all") -> dict:
	"""Fetch a list of popular places of interest in the user-specified city.
	   Args:
	      city_name: Name of the city.
	   Returns:
	   	   A dictionary containing location and places of interest information.
	"""

	if not consume_tool_budget("get_places_of_interest"):
		return {"error": "Tool call limit reached. Cannot fetch places of interest."}

	logger.info(f"Fetching places of interest for city: {city_name}")

	try:
		location = _geocode_city(city_name)
		lat = location["latitude"]
		lon = location["longitude"]

		# build appropriate search filters
		if place_type == "attractions":
			filters = {
				"history":[
					'["historic"]',
					'["tourism"~"museum|attraction"]'
				],
				"nature":[
					'["natural"]',
					'["tourism"~"viewpoint|nature_reserve"]'
				],
				"photography":[
					'["tourism"~"viewpoint|scenic|attraction"]',
					'["natural"~"peak|cliff"]',
					'["leisure"~"park|garden"]',
					'["historic"~"monument|castle"]'
				],
				"all":[
					'["tourism"~"museum|attraction|viewpoint|gallery|nature_reserve"]',
					'["natural"~"peak|cliff"]',
					'["leisure"~"park|garden"]',
					'["historic"~"monument|castle"]'
				]
			}

			selected_filters = filters.get(category, filters["all"])
		else:
			selected_filters = ['["amenity"~"restaurant|cafe|bar|fast_food"]']

		#construct Overpass QL query
		query_parts = []
		for tag_filter in selected_filters:
			query_parts.append(f"node{tag_filter}(around:1000,{lat},{lon});")
		query = f"[out:json];({''.join(query_parts)});out;"

		logger.info("Searching OSM for %s in %s", place_type,city_name)

		# response = requests.post(OVERPASS_URL, data={"data": query}, headers = {"User-Agent": "TripMate/1.0"}, timeout=35)
		data = None
		last_error = None

		for endpoint in OVERPASS_URLS:
			try:
				logger.info(f"Trying Overpass API endpoint: {endpoint}")
				response = requests.post(endpoint, data={"data": query}, headers = {"User-Agent": "TripMate/1.0"}, timeout=35)
				if response.status_code in [429,502,503,504]:
					logger.warning(f"Overpass API endpoint {endpoint} returned status code {response.status_code}. Trying next endpoint.")
					continue

				response.raise_for_status()
				data = response.json()
				logger.info("Overpass request successful!")
				break

			except requests.exceptions.Timeout as e:
				logger.error(f"Timeout error while fetching places of interest from {endpoint}: {e}")
				last_error = e
				continue

			except requests.exceptions.ConnectionError as e:
				logger.error(f"Connection error while fetching places of interest from {endpoint}: {e}")
				last_error = e
				continue

		if data is None:
			logger.error(f"All Overpass API endpoints failed. Last error: {last_error}")
			return {"error": f"All Overpass API endpoints failed. Last error: {last_error}"}

		places = []

		for element in data.get("elements", []):
			place = {
				"name": element.get("tags", {}).get("name", "Unknown"),
				"latitude": element.get("lat"),
				"longitude": element.get("lon"),
				"type": place_type,
				"category": category
			}
			places.append(place)

		return {
			"location": location,
			"places": places
		}
	except (requests.RequestException, ValueError, KeyError) as e:
		logger.error(f"Network error while fetching places of interest: {e}")
		return {"error": f"Network error while fetching places of interest: {e}"}


# TOOL2: ATTRACTIONS
def find_attractions(city_name: str, category: str = "all") -> dict:
	"""Fetch a list of popular attractions in the user-specified city.
	   Args:
	      city_name: Name of the city.
	      category: Category of attractions (e.g., history, nature, photography).
	   Returns:
	   	   A dictionary containing location and attractions information.
	"""

	if not consume_tool_budget("find_attractions"):
		return {"error": "Tool call limit reached. Cannot fetch attractions."}

	try:
		logger.info(f"Fetching attractions for city: {city_name} with category: {category}")
		return get_places_of_interest(city_name, place_type="attractions", category=category)
	except Exception as e:
		logger.error(f"Error while fetching attractions: {e}")
		return {"error": f"Error while fetching attractions: {e}"}


# TOOL 3: RESTAURANTS
def find_restaurants(city_name: str) -> dict:
	"""Fetch a list of popular restaurants in the user-specified city.
	   Args:
	      city_name: Name of the city.
	   Returns:
	   	   A dictionary containing location and restaurant information.
	"""

	if not consume_tool_budget("find_restaurants"):
		return {"error": "Tool call limit reached. Cannot fetch restaurants."}

	try:
		logger.info(f"Fetching restaurants for city: {city_name}")
		return get_places_of_interest(city_name, place_type="restaurants")
	except Exception as e:
		logger.error(f"Error while fetching restaurants: {e}")
		return {"error": f"Error while fetching restaurants: {e}"}

# TOOL 4: BUDGET ALLOCATION
def allocate_trip_budget(total_budget: float, num_days: int) -> dict:
	"""Allocate the user's total budget across different categories for the trip.
	   Args:
	      total_budget: Total budget for the trip.
	      num_days: Number of days for the trip.
	   Returns:
	   	   A dictionary containing the allocated budget for each category.
	"""
	if not consume_tool_budget("allocate_trip_budget"):
		return {"error": "Tool call limit reached. Cannot allocate trip budget."}

	try:
		logger.info(f"Allocating budget for trip: {total_budget} over {num_days} days")
		# Simple allocation logic - can be expanded based on user preferences
		transportation = total_budget * 0.3
		accommodation = total_budget * 0.4
		food = total_budget * 0.2
		activities = total_budget * 0.1

		return {
			"transportation": transportation,
			"accommodation": accommodation,
			"food": food,
			"activities": activities
		}
	except Exception as e:
		logger.error(f"Error while allocating trip budget: {e}")
		return {"error": f"Error while allocating trip budget: {e}"}