from decouple import config

class Settings:
    STEAM_API_KEY = config("STEAM_API_KEY", default="")
    SECRET_KEY = config("SECRET_KEY", default="your-secret-key-here")
    DATABASE_URL = config("DATABASE_URL", default="sqlite:///./steam_users.db")
    SITE_URL = config("SITE_URL", default="http://localhost:8000")
    FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

settings = Settings()
