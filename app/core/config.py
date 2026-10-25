# ==============================================================
# app/core/config.py
#
# WHAT THIS FILE DOES:
#   Reads all environment variables from your .env file,
#   validates them, and exposes them as a typed Python object
#   that every other file can import and use.
#
# CONCEPT — Why not just use os.getenv()?
#   You could call os.getenv("SECRET_KEY") anywhere in your code.
#   But that scatters configuration across the entire codebase,
#   gives you no validation, and no central place to see what
#   variables your app needs. A Settings class solves all of that.
# ==============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """
    CONCEPT — Class inheritance:
    By writing `class Settings(BaseSettings)`, our Settings class
    INHERITS all the behaviour of BaseSettings. That means Pydantic
    automatically reads .env, validates types, and raises clear
    errors if anything is missing. We get all of that for free.
    """

    # ---- Application ----
    # These have default values, so they are optional in .env
    APP_NAME: str = "Network Asset API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ---- Database ----
    # These have NO default value, so they are REQUIRED in .env.
    # If any is missing, the app refuses to start.
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "db"  # "db" inside Docker, "localhost" outside
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # ---- Security ----
    SECRET_KEY: str  # Required — no default
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Optional — defaults to 30

    # ---- CORS ----
    # Web origins (e.g. a front end at http://localhost:3000) that may call
    # the API from a browser. Empty means none: tools such as curl, Swagger
    # UI on the same host, and other servers are not affected by CORS.
    # Set it in .env as a JSON list: CORS_ORIGINS='["http://localhost:3000"]'
    CORS_ORIGINS: list[str] = []

    # ---- Pydantic configuration ----
    # This inner class tells Pydantic HOW to behave.
    # model_config is the modern Pydantic v2 way to set this.
    model_config = SettingsConfigDict(
        env_file=".env",  # Read from this file
        env_file_encoding="utf-8",  # File encoding
        case_sensitive=False,  # POSTGRES_USER and postgres_user are the same
        extra="ignore",  # Ignore any extra variables in .env we do not use
    )

    @property
    def DATABASE_URL(self) -> URL:
        """
        CONCEPT — @property:
        A @property lets you call a method as if it were a plain
        attribute. So instead of settings.DATABASE_URL(), you write
        settings.DATABASE_URL — no parentheses.

        We build the full connection URL here from the individual
        parts so the rest of the app never needs to construct it.

        The URL looks like this:
        postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
        The "+asyncpg" part tells SQLAlchemy to use the async driver.
        The app and Alembic both use it.

        CONCEPT — Why URL.create() instead of an f-string:
        A password such as "p@ss/word" contains characters that have
        a meaning inside a URL ("@" ends the password, "/" starts the
        database name). URL.create() escapes each part correctly,
        so any password works.
        """
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


# ==============================================================
# CONCEPT — Module-level singleton:
# We create ONE instance of Settings here at the bottom.
# Every other file imports THIS instance, not the class.
#
#   from app.core.config import settings
#   print(settings.APP_NAME)
#
# Because Python caches module imports, this object is created
# once and shared everywhere. This is called the Singleton pattern.
# ==============================================================
settings = Settings()
