from sqlalchemy import Column, ForeignKey, Integer, String

from app.db.base import Base


class Address(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    line1 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
