class OrderService:
    def __init__(self, order_repository):
        self.order_repository = order_repository

    async def create_order(self, payload: dict) -> dict:
        return await self.order_repository.create(payload)
