from fastapi import FastAPI
from pydantic import BaseModel

from ireland_visa_agent.config import settings
from pydantic import Field

from ireland_visa_agent.rag import Answer, answer_question

app = FastAPI(title=settings.app_name)


class HealthResponse(BaseModel):
    status: str
    environment: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

@app.post("/ask", response_model=Answer)
def ask(request: AskRequest) -> Answer:
    return answer_question(request.question)
