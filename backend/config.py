from decouple import config

class Settings:
    STEAM_API_KEY = config("STEAM_API_KEY", default="")
    SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")
    # Build MariaDB connection string from env vars
    DB_HOST = config("DB_HOST", default="mariadb")
    DB_PORT = config("DB_PORT", default="3306")
    DB_USER = config("DB_USER", default="thucs2pl")
    DB_PASSWORD = config("DB_PASSWORD", default="thucs2plpass")
    DB_NAME = config("DB_NAME", default="thucs2pl_db")
    DATABASE_URL = config(
        "DATABASE_URL",
        default=f"mariadb+mariadbconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SITE_URL = config("SITE_URL", default="http://localhost:8000")
    FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

settings = Settings()
