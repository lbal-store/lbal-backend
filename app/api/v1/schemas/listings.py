from pydantic import BaseModel


class ListingBase(BaseModel):
    title: str
    price: float


class ListingCreate(ListingBase):
    description: str | None = None


class ListingRead(ListingBase):
    id: int
