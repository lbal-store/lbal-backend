from sqlalchemy import Column, ForeignKey, Integer, String

from app.db.base import Base


class Shipment(Base):
    __tablename__ = 'shipments'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    carrier = Column(String)
