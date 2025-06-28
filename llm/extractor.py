import os
import asyncio
from typing import Dict
from together import Together, error
from dotenv import load_dotenv
import os
from .prompts import get_prompt_for


load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
async_client = Together(api_key=TOGETHER_API_KEY)

#si potrebbe anche togliere async
async def get_response_from_document(document_text: str, document_type: str, model: str) -> str:
    prompt = get_prompt_for(document_type) + "\n\n" + document_text
    print(get_prompt_for(document_type))
    for sleep_time in [1, 2, 4]:
        try:
            response = async_client.chat.completions.create(
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
            await asyncio.sleep(sleep_time)

    return response.choices[0].message.content