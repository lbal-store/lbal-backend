from fastapi import APIRouter


router = APIRouter(prefix='/users', tags=['users'])


@router.get('/ping')
async def ping_users() -> dict[str, str]:
    return {'router': 'users', 'status': 'ok'}
