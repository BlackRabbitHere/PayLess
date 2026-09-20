import re
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI

from payment_scraper.api.exception_handlers import install_exception_handlers
from payment_scraper.api.routes import router
from payment_scraper.core.logging_config import configure_logging, request_context
from payment_scraper.services.scraping_service import ScrapingService, build_service


def create_app(service: ScrapingService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        instance = service or build_service()
        configure_logging(instance.settings.log_level)
        app.state.service = instance
        try:
            yield
        finally:
            if service is None:
                instance.close()

    application = FastAPI(
        title="Payment Offer Scraper",
        version="1.0.0",
        description="Internal background ingestion interface; schemaVersion 1.",
        lifespan=lifespan,
    )
    @application.middleware("http")
    async def correlate(request, call_next):
        supplied = request.headers.get("X-Request-ID", "")
        request_id = supplied if re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", supplied) else str(uuid4())
        token = request_context.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_context.reset(token)

    application.include_router(router)
    install_exception_handlers(application)
    return application


app = create_app()
