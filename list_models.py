
import google.generativeai as genai
from app.core import config
import os

if config.settings.GEMINI_API_KEY:
    genai.configure(api_key=config.settings.GEMINI_API_KEY)
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
else:
    print("No API Key found")
