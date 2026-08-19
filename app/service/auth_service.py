import httpx

from fastapi import Request
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
from app.core.config import Settings
from app.core.redis import RedisConfig
from app.core.template import templates

class AuthService:
    def __init__(self):
        self.redis_config = RedisConfig()
        self.http_client = httpx.AsyncClient(timeout=30.0)

    @staticmethod
    def render_login(
            request: Request,
            error: str | None = None,
            message: str | None = None,
            username: str = "",
            status_code: int = 200,
    ):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": error,
                "username": username,
                "message": message,
            },
            status_code=status_code,
        )

    async def web_in_token(
        self,
        request: Request,
        username: str = "",
        password: str = "",
        ):
        normalized_username = username.strip()

        payload = {
            "authRealms": ["ENA"],
            "username": normalized_username,
            "password": password,
        }

        try:
            response = await self.http_client.post(
                Settings.WEBIN_TOKEN_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

        except httpx.RequestError as exc:
            return self.render_login(
                request= request,
                error="Unable to connect to Webin.",
                username=username,
                status_code=502,
            )

        if response.status_code in {401, 403}:
            return self.render_login(
                request=request,
                error="Wrong credentials. Please try again.",
                username=username,
                status_code=401,
            )

        if response.status_code != 200:
            return self.render_login(
                request=request,
                error="Authentication service returned an unexpected error.",
                username=username,
                status_code=502,
            )

        token = response.text.strip()

        if not token:
            return self.render_login(
                request=request,
                error="Wrong credentials. Please try again.",
                username=username,
                status_code=401,
            )

        try:
            await self.redis_config.cache_token(
                username=normalized_username,
                response= token
            )
        except RedisError:
            return self.render_login(
                request=request,
                error="Authentication service is temporarily unavailable. Please contact the administrator.",
                username=normalized_username,
                status_code=503,
            )

        request.session["message"] = (
            "You are successfully logged in. "
            "Please get back to your chat window."
        )

        return RedirectResponse(
            url="/login",
            status_code=303,
        )