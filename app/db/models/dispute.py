from sqlalchemy import Column, ForeignKey, Integer, String

from app.db.base import Base


class Dispute(Base):
    __tablename__ = 'disputes'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    status = Column(String, default='open')
