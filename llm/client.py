from openai import OpenAI
from config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    return _client

def chat(system_prompt: str, user_message: str, model: str = None, temperature: float = 0.3) -> str:
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=model or settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=800,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[LLM 不可用] {e}"
