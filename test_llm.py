import os
import sys

# Add project root to sys.path so we can import from core/config if needed, or just use decouple
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decouple import config
from anthropic import Anthropic

client = Anthropic(api_key=config("ANTHROPIC_API_KEY"))

try:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": 'Please return {"test": 123}'}]
    )
    print("RESPONSE TEXT:", repr(response.content[0].text))
except Exception as e:
    print("EXCEPTION:", repr(e))
