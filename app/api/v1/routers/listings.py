from fastapi import APIRouter


router = APIRouter(prefix='/listings', tags=['listings'])


@router.get('/ping')
async def ping_listings() -> dict[str, str]:
    return {'router': 'listings', 'status': 'ok'}
