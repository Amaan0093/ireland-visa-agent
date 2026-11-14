import ollama

from ireland_visa_agent.config import settings

_client = ollama.Client(host=settings.ollama_host)

def embed_documents(texts: list[str]) -> list[list[float]]:
    inputs = [f"search_document: {t}" for t in texts]
    return _client.embed(model=settings.embed_model, input=inputs).embeddings

def embed_query(text: str) -> list[float]:
    return _client.embed(model=settings.embed_model, input=f"search_query: {text}").embeddings[0]