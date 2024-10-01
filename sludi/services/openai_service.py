""" OpenAI API Commons """

import os
import json
import httplib2 as http

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = "gpt-3.5-turbo"

# ROLE
# 1. TASK + CONTEXT - You are an automated repair tool for Maven projects.
# 2. Format - You will receive two inputs: the exception details and the relevant block of code. Respond in two sections: 1. Error Analysis: Provide a concise explanation (maximum 100 words) identifying the root cause of the error based on the given exception and code. 2. Code Correction: Present the corrected version of the code, with changes clearly indicated by bolding the new or modified lines. Ensure the explanation is precise and that the corrected code adheres to best practices.
SYSTEM = "You are an automated repair tool for Maven projects. You will receive two inputs: the exception details and the relevant block of code. Respond in two sections: 1. Error Analysis: Provide a concise explanation (maximum 100 words) identifying the root cause of the error based on the given exception and code. 2. Code Correction: Present the corrected version of the code, with changes clearly indicated by bolding the new or modified lines. Ensure the explanation is precise and that the corrected code adheres to best practices."


url = "https://api.openai.com/v1/chat/completions"

def query(prompt: str) -> str:
    """
    OpenAI API for ChatGPT

    @param prompt: string
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": f"application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800
    }
    h = http.Http()
    response, content = h.request(url, "POST", json.dumps(data), headers)
    content_text = content.decode("utf-8")
    content_json = json.loads(content_text)
    return content_json["choices"][0]["message"]["content"]