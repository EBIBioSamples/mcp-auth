from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import Settings
from app.controller.web_in_controller import router

app = FastAPI(title="Python Login Portal")

app.add_middleware(
    SessionMiddleware,
    secret_key= Settings.session_secret,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router)