import ollama

from ireland_visa_agent.config import settings

_client = ollama.Client(host=settings.ollama_host)

def chat(system: str, user: str) -> str:
    response = _client.chat(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": 0},
    )
    return response.message.content