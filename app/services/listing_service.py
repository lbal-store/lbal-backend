class ListingService:
    def __init__(self, listing_repository):
        self.listing_repository = listing_repository

    async def list_active(self) -> list:
        return await self.listing_repository.list_active()
