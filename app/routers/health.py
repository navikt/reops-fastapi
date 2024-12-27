from fastapi import APIRouter

router = APIRouter()

@router.get("/api/isalive", tags=["Health"])
def read_isalive():
    return {"message": "Alive"}

@router.get("/api/isready", tags=["Health"])
def read_isready():
    return {"message": "Ready"}