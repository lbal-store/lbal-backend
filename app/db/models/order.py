from sqlalchemy import Column, ForeignKey, Integer, Numeric, String

from app.db.base import Base


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric(10, 2))
    status = Column(String, default='pending')
