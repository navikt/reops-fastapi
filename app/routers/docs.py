from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/", include_in_schema=False)
async def redirect_main() -> RedirectResponse:
    """Redirect users to the documentation."""
    return RedirectResponse(url="/docs")