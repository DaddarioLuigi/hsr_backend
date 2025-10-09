import os
import time
import logging
from together import Together, error
from dotenv import load_dotenv
from .prompts import PromptManager

logger = logging.getLogger(__name__)

class LLMExtractor:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "TOGETHER_API_KEY non configurata. "
                "Assicurati di impostare la variabile d'ambiente TOGETHER_API_KEY"
            )
        self.async_client = Together(api_key=api_key)
        self.prompt_manager = PromptManager()

    def get_response_from_document(self, document_text, document_type, model):
        prompt = self.prompt_manager.get_prompt_for(document_type) + "\n\n" + document_text
        schema = self.prompt_manager.get_schema_for(document_type)

        response = None
        last_error = None
        
        for attempt, sleep_time in enumerate([0, 1, 2, 4], start=1):
            try:
                if sleep_time > 0:
                    logger.warning(f"Retry {attempt}/4 dopo {sleep_time}s per {document_type}")
                    time.sleep(sleep_time)
                
                response = self.async_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={
                        "type": "json_schema",
                        "schema": schema
                    },
                    temperature=0.7,
                    top_p=0.2,
                    max_tokens=8192
                )
                logger.info(f"Estrazione completata per {document_type} (tentativo {attempt})")
                break
            except error.RateLimitError as e:
                last_error = e
                logger.error(f"Rate limit error tentativo {attempt}/4: {e}")
            except Exception as e:
                last_error = e
                logger.error(f"Errore tentativo {attempt}/4 per {document_type}: {e}")
                if attempt == 4:
                    raise
        
        if response is None:
            raise RuntimeError(
                f"Impossibile ottenere risposta dall'LLM dopo 4 tentativi. "
                f"Ultimo errore: {last_error}"
            )
        
        return response.choices[0].message.content
