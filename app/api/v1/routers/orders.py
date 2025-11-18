from fastapi import APIRouter


router = APIRouter(prefix='/orders', tags=['orders'])


@router.get('/ping')
async def ping_orders() -> dict[str, str]:
    return {'router': 'orders', 'status': 'ok'}
