from pydantic import BaseModel, Field


class ApprovalIn(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)
