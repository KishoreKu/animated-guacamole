import os
from dotenv import load_dotenv
from google import genai

# Try to load from backend/.env if it exists
if os.path.exists('backend/.env'):
    load_dotenv('backend/.env')
else:
    load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

if not api_key:
    exit(1)

client = genai.Client(api_key=api_key)

try:
    print("Listing models...")
    for model in client.models.list():
        print(f"- {model.name}")
except Exception as e:
    print(f"Error: {e}")
