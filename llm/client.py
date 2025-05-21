# llm/client.py

import openai

class LLMClient:
    """
    LLM client using OpenAI API. 
    ATTENZIONE: la chiave è hard-codata per test rapidi, 
    revocala subito dopo aver finito!
    """
    def __init__(self, model="gpt-4.1"):
        # Hard-code temporaneo della chiave
        openai.api_key = "ciao"
        self.model = model

    def infer(self, prompt: str) -> str:
        """
        Invia il prompt all’API OpenAI e restituisce il contenuto generato.
        Usa il nuovo client openai>=1.0.0.
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content.strip()
            print(f"[LLMClient] Ricevuto (max 100 car.): {content[:100]}...")
            return content
        except Exception as e:
            print(f"[LLMClient Error] {type(e).__name__}: {e}")
            return ""
