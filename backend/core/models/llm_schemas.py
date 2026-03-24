"""
Pydantic schemas for structured LLM outputs.
"""
from pydantic import BaseModel


class InterviewTurnResponse(BaseModel):
    """Structured response for one interview turn."""

    acknowledgement: str
    feedback_short: str
    next_question: str
