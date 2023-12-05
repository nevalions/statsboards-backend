from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from src.seasons import api_pars_season_router, api_season_router

app = FastAPI()

app.include_router(api_season_router)

app.include_router(api_pars_season_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#hel
