from src.core import db
from src.matches.crud_router import MatchCRUDRouter
from src.matches.db_services import MatchServiceDB
from src.matches.parser_router import MatchParserRouter
from src.matches.websocket_router import MatchWebSocketRouter

match_service = MatchServiceDB(db)
api_match_crud_router = MatchCRUDRouter(match_service).route()
api_match_websocket_router = MatchWebSocketRouter(match_service).route()
api_match_parser_router = MatchParserRouter(match_service).route()
