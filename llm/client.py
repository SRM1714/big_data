# import openai
# import os
# import requests
# from config import MODEL_NAME

# class LLMClient:
#     def __init__(self, model=MODEL_NAME):
#         self.model = model
#         openai.api_key = os.getenv("OPENAI_API_KEY")

#     def infer(self, prompt):
#         if self.model=="gpt4.1":
#             try:
#                 response = openai.chat.completions.create(
#                     model=self.model,
#                     messages=[{"role": "user", "content": prompt}],
#                 )
#                 content = response.choices[0].message.content.strip()
#                 print(f"[LLMClient] Received response: {content[:100]}...")
#                 return content
#             except Exception as e:
#                 print(f"[LLMClient Error] {type(e).__name__}: {e}")
#                 return ""

#         else:
#             response = requests.post(
#                 "http://localhost:11434/api/generate",
#                 json={"model": self.model, "prompt": prompt, "stream": False}
#             )
#             return response.json()["response"]

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