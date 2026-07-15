"""AI assist request schema."""

from pydantic import BaseModel, Field


class AiAssistRequest(BaseModel):
    field_label: str = ""
    field_context: str = ""
    current_text: str = ""
    action: str = ""
    user_prompt: str | None = Field(default=None, max_length=2000)
