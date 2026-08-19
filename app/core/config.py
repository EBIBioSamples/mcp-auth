import os

from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    WEBIN_TOKEN_URL: str = os.getenv(
        "WEBIN_TOKEN_URL",
        "https://wwwdev.ebi.ac.uk/ena/submit/webin/auth/token",
    )
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0",
    )
    session_secret: str = os.getenv(
        "SESSION_SECRET",
        "change-this-development-secret",
    )