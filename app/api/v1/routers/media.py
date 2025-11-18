from fastapi import APIRouter


router = APIRouter(prefix='/media', tags=['media'])


@router.get('/ping')
async def ping_media() -> dict[str, str]:
    return {'router': 'media', 'status': 'ok'}
