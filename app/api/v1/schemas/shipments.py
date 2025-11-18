from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    order_id: int
    carrier: str
