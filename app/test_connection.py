# app/test_connection.py

import ollama
import os
import sys

# Get the Ollama URL from the same environment variable your app uses
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

print("--- Starting Connection Test ---")

if not OLLAMA_BASE_URL:
    print("🔥 ERROR: OLLAMA_BASE_URL environment variable is not set.", file=sys.stderr)
    sys.exit(1)

try:
    print(f"Attempting to connect to Ollama at: {OLLAMA_BASE_URL}")
    
    # Create a client pointing directly to the Ollama container
    client = ollama.Client(host=OLLAMA_BASE_URL)
    
    # Perform the simplest possible command
    client.list()
    
    print("✅ SUCCESS: Successfully connected to the Ollama server.")

except Exception as e:
    print(f"🔥 FAILED: An error occurred while trying to connect.", file=sys.stderr)
    print(f"Error details: {e}", file=sys.stderr)
    sys.exit(1)
