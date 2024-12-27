from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import apps, events, health
from .database import engine
from .config import logger

app = FastAPI()

app.include_router(apps)
app.include_router(events)
app.include_router(health)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Content-Type"],
)

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        content={"message": "An internal server error occurred. Please try again later.", "details": str(exc)},
        status_code=500
    )

@app.on_event("startup")
async def startup():
    engine.connect()
    logger.info("Database connection established.")

@app.on_event("shutdown")
def shutdown():
    if engine.pool:
        engine.pool.dispose()
        logger.info("Database connection pool disposed.")