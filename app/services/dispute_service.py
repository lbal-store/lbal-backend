class DisputeService:
    def __init__(self, dispute_repository):
        self.dispute_repository = dispute_repository

    async def open_dispute(self, payload: dict) -> dict:
        return await self.dispute_repository.create(payload)
