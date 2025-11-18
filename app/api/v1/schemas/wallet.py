from pydantic import BaseModel


class WalletBalance(BaseModel):
    user_id: int
    balance: float
