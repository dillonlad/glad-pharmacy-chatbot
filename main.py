from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from logging import StreamHandler, DEBUG, INFO, getLogger, Logger

from config import get_config
from routers.chatbot.api_router import router as chatbot_router
from routers.orders.api_router import router as orders_router
from routers.updates.api_router import router as updates_router
from routers.whatsapp.api_router import router as whatsapp_router


from pydantic import BaseModel

from auth import verify_token

def create_app_uvicorn() -> FastAPI:
    """
    Creates a FastAPI app configured for Uvicorn.
    """

    return create_app(getLogger("uvicorn"))


def create_app(logger: Logger = None) -> FastAPI:
    """
    Creates the FastAPI app.

    :return: FastAPI app.
    """

    # Get config.
    config = get_config()

    # Set OpenAPI route.
    openapi_url = "/openapi.json"
    docs_url = "/docs"
    redoc_url = "/redoc"

    # Create app.
    app = FastAPI(
        title=config.APP_NAME,
        debug=config.DEBUG,
        version=config.VERSION,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    # Sort out logger.
    if logger is None:
        logger = getLogger("fastapi")
        handler = StreamHandler(stdout)
        logger.addHandler(handler)
    logger.setLevel(DEBUG if config.DEBUG else INFO)

    # Add custom exception handlers here

    # Wire up routes.
    app.include_router(chatbot_router)
    app.include_router(updates_router)
    app.include_router(orders_router)
    app.include_router(whatsapp_router)

    # Set CORS access (Allows access from a front-end hosted on a separate domain)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ORIGINS,
        allow_credentials=config.ALLOW_CREDENTIALS,
        allow_methods=config.ALLOWED_METHODS,
        allow_headers=config.ALLOWED_HEADERS,
    )

    return app
