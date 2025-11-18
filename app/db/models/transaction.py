from sqlalchemy import Column, ForeignKey, Integer, Numeric, String

from app.db.base import Base


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('wallets.id'))
    amount = Column(Numeric(10, 2))
    type = Column(String)
