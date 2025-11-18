from sqlalchemy import Column, ForeignKey, Integer, String

from app.db.base import Base


class ListingImage(Base):
    __tablename__ = 'listing_images'

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'))
    url = Column(String, nullable=False)
