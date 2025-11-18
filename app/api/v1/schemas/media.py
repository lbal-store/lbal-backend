from pydantic import BaseModel


class MediaUpload(BaseModel):
    listing_id: int
    url: str
