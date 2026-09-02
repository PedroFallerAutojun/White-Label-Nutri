"""Configuração de produção de uma instância (empresa cliente).

Cada empresa roda seu próprio deploy com suas variáveis de ambiente:
SECRET_KEY, ALLOWED_HOSTS e DATABASE_URL são obrigatórias.
"""
from config.settings.base import *  # noqa: F401,F403

# Falha cedo se as variáveis obrigatórias não estiverem definidas.
SECRET_KEY = env("SECRET_KEY")  # noqa: F405
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405
DEBUG = False

# HTTPS / proxy (Heroku, Fly, Render e afins encerram TLS antes da aplicação)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if host != "*"]

# HSTS — comece com um valor baixo e aumente após confirmar que todo o tráfego é HTTPS.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(  # noqa: F405
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = False

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Sessão expira em 12 h de inatividade.
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=12 * 60 * 60)  # noqa: F405
SESSION_SAVE_EVERY_REQUEST = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "padrao": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "padrao"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},  # noqa: F405
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
