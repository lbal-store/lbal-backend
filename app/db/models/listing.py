from sqlalchemy import Column, ForeignKey, Integer, Numeric, String

from app.db.base import Base


class Listing(Base):
    __tablename__ = 'listings'

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
