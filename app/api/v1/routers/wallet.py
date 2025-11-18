from fastapi import APIRouter


router = APIRouter(prefix='/wallet', tags=['wallet'])


@router.get('/ping')
async def ping_wallet() -> dict[str, str]:
    return {'router': 'wallet', 'status': 'ok'}
