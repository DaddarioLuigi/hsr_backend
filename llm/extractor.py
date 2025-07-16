import os
from together import Together, error
from dotenv import load_dotenv
from .prompts import PromptManager

class LLMExtractor:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("TOGETHER_API_KEY")
        self.async_client = Together(api_key=api_key)
        self.prompt_manager = PromptManager()

    def get_response_from_document(self, document_text, document_type, model):
        prompt = self.prompt_manager.get_prompt_for(document_type) + "\n\n" + document_text
        for sleep_time in [1, 2, 4]:
            try:
                response = self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_schema"},
                    temperature=0.1,
                    top_p=1,
                    max_tokens=8192
                )
                break
            except error.RateLimitError as e:
                print(e)
        return response.choices[0].message.content