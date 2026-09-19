from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_scraper.api.exception_handlers import install_exception_handlers
from payment_scraper.api.routes import router
from payment_scraper.core.logging_config import configure_logging
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
    application.include_router(router)
    install_exception_handlers(application)
    return application


app = create_app()
