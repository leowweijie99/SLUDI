""" Anthropic API Commons """

import os
import json
import httplib2 as http

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')
MODEL = "claude-3-5-sonnet-20240620"


# SYSTEM prompt
SYSTEM = "You are an automated repair tool for Maven projects. You will receive two inputs: the exception details and the relevant block of code. Respond in two sections: 1. Error Analysis: Provide a concise explanation (maximum 100 words) identifying the root cause of the error based on the given exception and code. 2. Code Correction: Present the corrected version of the code, with changes clearly indicated by bolding the new or modified lines. Ensure the explanation is precise and that the corrected code adheres to best practices."

url = "https://api.anthropic.com/v1/messages"

def query(prompt: str) -> str:
    """
    Anthropic API for Claude AI

    @param prompt: string
    """
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "system": SYSTEM,
        "messages": [
        {"role": "user", "content": prompt}
        ],
        "max_tokens": 800,
        "temperature": 0,
    }
    h = http.Http()
    response, content = h.request(url, "POST", json.dumps(data), headers)
    content_text = content.decode("utf-8")
    content_json = json.loads(content_text)
    return content_json['content'][0]['text']