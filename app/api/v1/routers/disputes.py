from fastapi import APIRouter


router = APIRouter(prefix='/disputes', tags=['disputes'])


@router.get('/ping')
async def ping_disputes() -> dict[str, str]:
    return {'router': 'disputes', 'status': 'ok'}
