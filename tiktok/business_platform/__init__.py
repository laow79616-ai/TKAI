"""TKAI Business Platform V1.0 product layer."""

from .api import GET_ROUTES, openapi_contract, register_business_platform_routes
from .service import BusinessPlatform

__all__ = [
    "BusinessPlatform",
    "GET_ROUTES",
    "openapi_contract",
    "register_business_platform_routes",
]
