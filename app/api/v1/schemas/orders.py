from pydantic import BaseModel


class OrderCreate(BaseModel):
    listing_id: int
    quantity: int = 1


class OrderRead(BaseModel):
    id: int
    status: str
