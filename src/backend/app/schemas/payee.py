from pydantic import BaseModel, ConfigDict, Field


class PayeeIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    xrpl_address: str = Field(min_length=25, max_length=64)


class PayeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mandate_id: int
    name: str
    xrpl_address: str
    active: bool
