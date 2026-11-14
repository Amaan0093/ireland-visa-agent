from fastapi import FastAPI
from pydantic import BaseModel

from ireland_visa_agent.config import settings

app = FastAPI(title=settings.app_name)


class HealthResponse(BaseModel):
    status: str
    environment: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
