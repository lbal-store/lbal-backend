class WalletService:
    def __init__(self, wallet_repository):
        self.wallet_repository = wallet_repository

    async def get_balance(self, user_id: int) -> dict:
        return await self.wallet_repository.get_balance(user_id)
