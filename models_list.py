import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

# Configure Gemini
genai.configure(api_key=api_key)

# Fetch available models
models = genai.list_models()

free_models = []

for model in models:
    # Only text / multimodal generation models
    if "generateContent" in model.supported_generation_methods:
        # Heuristic: free models do NOT contain "pro" or "1.5-pro"
        if not any(x in model.name.lower() for x in ["pro", "ultra"]):
            free_models.append(model.name)

print("Free Gemini models available via API:\n")
for m in free_models:
    print("-", m)
