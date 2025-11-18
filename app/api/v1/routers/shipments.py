from fastapi import APIRouter


router = APIRouter(prefix='/shipments', tags=['shipments'])


@router.get('/ping')
async def ping_shipments() -> dict[str, str]:
    return {'router': 'shipments', 'status': 'ok'}
