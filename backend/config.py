import json
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

    MATCHZY_WEBHOOK_TOKEN = config("MATCHZY_WEBHOOK_TOKEN", default="")

    SERVER_VOTE_TIMEOUT_SECONDS = config("SERVER_VOTE_TIMEOUT_SECONDS", default=30, cast=int)

    # ---- Multi-provider server provisioning ----

    # SERVER_HOSTS defines all available game servers players can vote for.
    # Each entry maps a vote key to a provider mode and display label.
    # Example:
    # {
    #   "local":     {"mode": "local_docker",  "label": "本地服务器"},
    #   "server_b":  {"mode": "remote_docker", "label": "服务器B"},
    #   "tencent":   {"mode": "tencent_as",    "label": "腾讯云服务器"},
    #   "aliyun":    {"mode": "aliyun_eci",    "label": "阿里云ECI"}
    # }
    _server_hosts_raw = config(
        "SERVER_HOSTS",
        default='{"local": {"mode": "local_docker", "label": "本地服务器"}}',
    )
    SERVER_HOSTS: dict = json.loads(_server_hosts_raw) if _server_hosts_raw else {}

    SERVER_DEFAULT = config("SERVER_DEFAULT", default="local")

    # ---- Docker settings (shared by local & remote providers) ----

    CS2_DOCKER_IMAGE = config("CS2_DOCKER_IMAGE", default="")
    CS2_DOCKER_CPU = config("CS2_DOCKER_CPU", default=4, cast=int)
    CS2_DOCKER_MEMORY = config("CS2_DOCKER_MEMORY", default="8g")

    # ---- Local Docker ----

    LOCAL_DOCKER_PUBLIC_IP = config("LOCAL_DOCKER_PUBLIC_IP", default="")

    # ---- Remote Docker (server B via SSH) ----

    REMOTE_DOCKER_HOST = config("REMOTE_DOCKER_HOST", default="")
    REMOTE_DOCKER_SSH_USER = config("REMOTE_DOCKER_SSH_USER", default="root")
    REMOTE_DOCKER_SSH_PORT = config("REMOTE_DOCKER_SSH_PORT", default=22, cast=int)
    REMOTE_DOCKER_SSH_KEY = config("REMOTE_DOCKER_SSH_KEY", default="~/.ssh/id_rsa")
    REMOTE_DOCKER_PUBLIC_IP = config("REMOTE_DOCKER_PUBLIC_IP", default="")

    # ---- Tencent Cloud AS (弹性伸缩) ----

    TENCENT_SECRET_ID = config("TENCENT_SECRET_ID", default="")
    TENCENT_SECRET_KEY = config("TENCENT_SECRET_KEY", default="")
    TENCENT_AS_REGION = config("TENCENT_AS_REGION", default="ap-beijing")
    # Pre-configured scaling group whose launch template runs the CS2 image.
    # Provider sets MinSize=0/MaxSize=1 and DesiredCapacity=1 on match start,
    # then scales back to 0 on match end.
    TENCENT_AS_GROUP_ID = config("TENCENT_AS_GROUP_ID", default="")
    TENCENT_AS_LAUNCH_CONFIG_ID = config("TENCENT_AS_LAUNCH_CONFIG_ID", default="")
    # Seconds to poll for instance IN_SERVICE state before giving up
    TENCENT_AS_PROVISION_TIMEOUT = config("TENCENT_AS_PROVISION_TIMEOUT", default=300, cast=int)

    # ---- Alibaba Cloud ECI (弹性容器实例) ----

    ALIYUN_ACCESS_KEY_ID = config("ALIYUN_ACCESS_KEY_ID", default="")
    ALIYUN_ACCESS_KEY_SECRET = config("ALIYUN_ACCESS_KEY_SECRET", default="")
    ECI_REGION = config("ECI_REGION", default="cn-beijing")
    ECI_SECURITY_GROUP_ID = config("ECI_SECURITY_GROUP_ID", default="")
    ECI_VSWITCH_ID = config("ECI_VSWITCH_ID", default="")
    # Optional: pin instance type (e.g. "ecs.g6.large"). Leave empty for auto.
    ECI_INSTANCE_TYPE = config("ECI_INSTANCE_TYPE", default="")
    ECI_AUTO_CREATE_EIP = config("ECI_AUTO_CREATE_EIP", default=True, cast=bool)
    ECI_EIP_BANDWIDTH = config("ECI_EIP_BANDWIDTH", default=10, cast=int)
    ECI_PROVISION_TIMEOUT = config("ECI_PROVISION_TIMEOUT", default=300, cast=int)


settings = Settings()
