import openai

class LLMClient:
    """
    LLM client using OpenAI API. API key is embedded directly for testing purposes.
    Remove hard-coded key for production use.
    """
    def __init__(self, model="gpt-4.1"):
        # Directly set the API key (hard-coded for quick test)
        openai.api_key = "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"
        self.model = model

    def infer(self, prompt):
        """
        Send a prompt to the OpenAI API and return the generated content.
        Uses the openai-python v1 interface.
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.choices[0].message.content.strip()
            print(f"[LLMClient] Received response: {content[:100]}...")
            return content
        except Exception as e:
            print(f"[LLMClient Error] {type(e).__name__}: {e}")
            return ""
