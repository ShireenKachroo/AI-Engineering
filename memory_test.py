from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


messages = []
messages.append({
	"role":"user",
	"parts": [{"text": "Hi, my name is Shireen!"}]
})
messages.append({
	"role":"model",
	"parts": [{"text": "Hello Shireen, nice to meet you!"}]
})
messages.append({
	"role":"user",
	"parts": [{"text": "I am learning AI engineering."}]
})
messages.append({
	"role":"model",
	"parts": [{"text": "That's great! AI Engineering is an exciting field."}]
})

# print(messages)

messages.append({
    "role": "user",
    "parts": [{"text": "What am I learning?"}]
})

# send complete conversation history to Gemini
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=messages
)

print("Gemini:", response.text)

# store Gemini's response in conversation history
messages.append({
    "role": "model",
    "parts": [{"text": response.text}]
})