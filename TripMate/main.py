# GEMINI Client, Chat Session, Conversation Loop
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import (get_weather, find_attractions, find_restaurants, allocate_trip_budget)
from tools import reset_tool_call_budget
import logging
from colorama import Fore, Style, just_fix_windows_console

just_fix_windows_console()

class ColoredFormatter(logging.Formatter):
	COLORS = {
		logging.DEBUG: Fore.WHITE,
		logging.INFO: Fore.CYAN,
		logging.WARNING: Fore.YELLOW,
		logging.ERROR: Fore.RED,
		logging.CRITICAL: Fore.RED + Style.BRIGHT
	}
	def format(self, record):
		color = self.COLORS.get(
			record.levelno,
			Fore.WHITE
		)
		message = super().format(record)
		return color + message + Style.RESET_ALL

handler = logging.StreamHandler()
handler.setFormatter(
	ColoredFormatter(
		"%(asctime)s | %(levelname)s | %(message)s",
		datefmt = "%H:%M:%S"
	)
)

root_logger = logging.getLogger()

root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(handler)


# load api key
load_dotenv()
api_key = os.getenv("GENAI_API_KEY")

if not api_key:
	raise ValueError("GENAI_API_KEY not found in environment variables.")

#initialize gemini client
client = genai.Client(api_key=api_key)

#create chat session with our tool
chat = client.chats.create(
	model = "gemini-3.6-flash",
	config=types.GenerateContentConfig(
		system_instruction = """"You are TripMate, a travel assistant that provides weather forecasts for cities around the world.
								Help users plan practical trips based on their destination, duration, budget and interests.
								Before performing tool-based actions, briefly explain which information you need and which tools you intend to use.
								Do not expose private internal reasoning. Provide concise action summaries, not lengthy reasoning transcripts.

								Available Tools:
								- get_weather: Fetch weather information for a specified city.
								- find_attractions: Fetch a list of popular attractions in the user-specified city.
								- find_restaurants: Fetch a list of popular restaurants in the user-specified city.
								- allocate_trip_budget: Allocate the user's total budget across different categories for the trip.

								Instructions:
								- Use tools whenever relevant.
								- Combine information from multiple tools when planning trips.
								- Never invent API results.
								- Clearly distinguish sourced information from estimates.
								- Do not invent entrance fees, opening hours, restaurant prices, or any other information.
								- Budget allocation is an estimate, not verified local pricing.
								- Explain weather codes in understandable language.
								- Give practical, day-wise iteneraries.
							""",
		tools = [get_weather, find_attractions, find_restaurants, allocate_trip_budget],
		automatic_function_calling = (types.AutomaticFunctionCallingConfig(maximum_remote_calls=5))
	)
)

# CHAT LOOP
print("\nGhoomi Ghoomi Chalein?")
print("Your Ghoomi Ghoomi Assistant is Ready.")
print("Type 'exit' to quit.")

while True:
	user_msg = input("You: ").strip()

	if user_msg.lower() == "exit":
		print("TripMate: Safe travels! Goodbye!")
		break
	if not user_msg:
		continue
	try:
		reset_tool_call_budget()
		response = chat.send_message(user_msg)
		print("TripMate:", response.text)
		print()
	except Exception as e:
		print(f"\n Something went wrong:{e}\n")