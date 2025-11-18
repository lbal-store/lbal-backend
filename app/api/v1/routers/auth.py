from fastapi import APIRouter


router = APIRouter(prefix='/auth', tags=['auth'])


@router.get('/ping')
async def ping_auth() -> dict[str, str]:
    return {'router': 'auth', 'status': 'ok'}
