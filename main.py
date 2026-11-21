import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()  # load env vars ... gemini api

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
	raise ValueError("GEMINI_API_KEY not found in environment variables.")

# create gemini client
client = genai.Client(api_key = api_key)

# function for tool calling
def multiply_numbers(a:int, b:int)->int:
	"""
	Multiply two integers and return their product.

    Args:
        a: The first integer.
        b: The second integer.
	"""
	print(f"[TOOL EXECUTED] Multiplying {a} and {b}")
	return a*b

# create chat session
chat = client.chats.create(
	model = "gemini-3.6-flash",
	config = types.GenerateContentConfig(
		system_instruction = """
        You are a friendly AI Engineering mentor.

        - Explain concepts in simple language.
        - Use practical examples wherever possible.
        - Avoid unnecessary theoretical explanations.
        - When helping with coding problems, give hints first.
        - Encourage the user to think independently.
        """,
		tools = [multiply_numbers]
	)
)

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