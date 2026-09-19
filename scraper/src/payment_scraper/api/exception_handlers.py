import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from payment_scraper.api.schemas import ApiErrorResponse
from payment_scraper.core.enums import ErrorCode
from payment_scraper.core.models import ScrapeError

logger = logging.getLogger(__name__)


def install_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Do not echo request bodies, arbitrary URLs or Pydantic exception internals.
        body = ApiErrorResponse(
            errors=[ScrapeError(code=ErrorCode.BAD_REQUEST, message="Request does not match the v1 schema.")]
        )
        return JSONResponse(status_code=422, content=body.model_dump(mode="json", by_alias=True))

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logger.error("api_failed", exc_info=(type(exc), exc, exc.__traceback__))
        body = ApiErrorResponse(
            errors=[ScrapeError(code=ErrorCode.INTERNAL_ERROR, message="An internal service error occurred.")]
        )
        return JSONResponse(status_code=500, content=body.model_dump(mode="json", by_alias=True))
