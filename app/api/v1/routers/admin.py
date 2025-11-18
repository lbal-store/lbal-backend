from fastapi import APIRouter


router = APIRouter(prefix='/admin', tags=['admin'])


@router.get('/ping')
async def ping_admin() -> dict[str, str]:
    return {'router': 'admin', 'status': 'ok'}
