from .views import (
    api_match_crud_router,
    api_match_parser_router,
    api_match_websocket_router,
)

# from .views import template_match_router
__all__ = ["api_match_crud_router", "api_match_parser_router", "api_match_websocket_router"]
