import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # load env vars ... gemini api

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
	raise ValueError("GEMINI_API_KEY not found in environment variables.")

# create gemini client
client = genai.Client(api_key = api_key)

# create chat session
chat = client.chats.create(model = "gemini-3.6-flash")

print("Gemini chatbot is ready!")
print("Type 'exit' to quit\n")

while True:
	user_msg = input("You : ").strip()

	if user_msg.lower() == "exit":
		print("Goodbye!")
		break
	
	if not user_msg:
		continue

	try:
		response = chat.send_message(user_msg)
		print("Gemini: ", response.text)
		print()

	except Exception as e:
		print("Something went wrong: ", e)