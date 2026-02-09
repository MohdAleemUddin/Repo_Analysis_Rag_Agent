from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.routes import router as api_router
from .indexing import indexer
from .security import TOKEN_HEADER, verify_token


def _error_response(error_code: str, message: str, remediation: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "remediation": remediation,
        },
    )


def create_app() -> FastAPI:
    app = FastAPI()
    indexer.reset_indexer_state()

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error_code" in exc.detail:
            return _error_response(
                exc.detail["error_code"],
                exc.detail["message"],
                exc.detail["remediation"],
                exc.status_code,
            )
        return _error_response(
            "UNKNOWN_ERROR",
            "Unhandled error.",
            "Retry the request.",
            exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        return _error_response(
            "INVALID_INPUT",
            f"Validation error: {exc.errors()}",
            "Ensure the request body matches the expected schema.",
            400,
        )

    app.include_router(api_router)

    return app


app = create_app()
