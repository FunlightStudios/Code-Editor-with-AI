import requests

class ChatGPTAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = 'https://api.openai.com/v1/chat/completions'

    def get_response(self, prompt):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 150
        }
        response = requests.post(self.url, headers=headers, json=data)
        return response.json() if response.status_code == 200 else None
