""" OpenAI API Commons """

import os
import json
import httplib2 as http

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('OPENAI_KEY')
MODEL = "gpt-3.5-turbo"

# How you want the AI to respond like.
ROLE = "You are a automated repair program."


url = "https://api.openai.com/v1/chat/completions"

def query(prompt: str) -> str:
    """
    OpenAI API wrapper

    @param prompt: string
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": f"application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": ROLE},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300
    }
    h = http.Http()
    response, content = h.request(url, "POST", json.dumps(data), headers)
    content_text = content.decode("utf-8")
    content_json = json.loads(content_text)
    return content_json["choices"][0]["message"]["content"]