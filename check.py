"""Quick connectivity check for the Gemini API (set GEMINI_API_KEY in .env)."""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")

model = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")
client = genai.Client(api_key=api_key)
resp = client.models.generate_content(model=model, contents="Say hello in one word.")
print(resp.text)
