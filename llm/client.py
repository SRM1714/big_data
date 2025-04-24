import requests
from config import MODEL_NAME

class LLMClient:
    def __init__(self, model=MODEL_NAME):
        self.model = model

    def infer(self, prompt):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json()["response"]
