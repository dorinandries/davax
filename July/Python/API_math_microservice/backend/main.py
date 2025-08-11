from fastapi import FastAPI
from config.settings import Settings
from core.logger import setup_logging
from core.metrics import setup_metrics
from api.controllers import router

def create_app() -> FastAPI:
    settings = Settings()
    logger = setup_logging(settings, log_days=1)  # Change log_days as needed
    app = FastAPI(
        title="Tema python",
        version="1.0.0",
        description="API for math operations: Pow, Fibonacci, Factorial",
    )
    # CORS
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info(f"Incoming request {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Completed {response.status_code}")
        return response

    # Metrics
    setup_metrics(app)

    # Exception handler
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error. Contact admin!"}
        )

    app.include_router(router, prefix="/api/v1")
    return app
