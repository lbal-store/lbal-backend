from pydantic import BaseModel


class DisputeCreate(BaseModel):
    order_id: int
    reason: str


class DisputeRead(BaseModel):
    id: int
    status: str
