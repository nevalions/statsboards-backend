
from src.core import db

# from src.core.config import templates
from src.matches.crud_router import MatchCRUDRouter
from src.matches.db_services import MatchServiceDB
from src.matches.parser_router import MatchParserRouter
from src.matches.websocket_router import MatchWebSocketRouter

# class MatchTemplateRouter(
#     MinimalBaseRouter[
#         MatchSchema,
#         MatchSchemaCreate,
#         MatchSchemaUpdate,
#     ]
# ):
#     def __init__(self, service: MatchServiceDB):
#         super().__init__(
#             "/matches",
#             ["matches"],
#             service,
#         )
#
#     def route(self):
#         router = super().route()
#
#         @router.get(
#             "/all/",
#         )
#         async def get_all_matches_endpoint(request: Request):
#             template = templates.TemplateResponse(
#                 name="/matches/display/all-matches.html",
#                 context={"request": request},
#                 status_code=200,
#             )
#             return template
#
#         @router.get(
#             "/id/{match_id}/scoreboard/",
#         )
#         async def edit_match_data_endpoint(
#             request: Request,
#             match_id: int,
#         ):
#             template = templates.TemplateResponse(
#                 name="/scoreboards/display/score-main.html",
#                 context={"request": request},
#                 status_code=200,
#             )
#             return template
#
#         @router.get(
#             "/id/{match_id}/scoreboard/hd/",
#         )
#         async def display_fullhd_match_data_endpoint(
#             request: Request,
#             match_id: int,
#         ):
#             template = templates.TemplateResponse(
#                 name="/scoreboards/display/score-fullhd.html",
#                 context={"request": request},
#                 status_code=200,
#             )
#             return template
#
#         return router


match_service = MatchServiceDB(db)
api_match_crud_router = MatchCRUDRouter(match_service).route()
api_match_websocket_router = MatchWebSocketRouter(match_service).route()
api_match_parser_router = MatchParserRouter(match_service).route()
# template_match_router = MatchTemplateRouter(match_service).route()
