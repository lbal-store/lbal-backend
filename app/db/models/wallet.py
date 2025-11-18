from sqlalchemy import Column, ForeignKey, Integer, Numeric

from app.db.base import Base


class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    balance = Column(Numeric(10, 2), default=0)
