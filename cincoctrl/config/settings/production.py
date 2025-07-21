# ruff: noqa: E501
# import logging

# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
# from sentry_sdk.integrations.logging import LoggingIntegration

from .base import *  # noqa: F403
from .base import DATABASES
from .base import INSTALLED_APPS
from .base import env

DEBUG = True
CINCO_ENVIRONMENT = "prd"
AIRFLOW_PROJECT_NAME = "cinco-prd"

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "oac.cdlib.org",
    "*",
]

# We need the ALB's DNS record & public IP in ALLOWED_HOSTS, but neither
# are persistent at the moment - revisit once we have a persistent DNS
# record.

# When/if we lock down ALLOWED_HOSTS, we'll need to add the following so
# that the ECS task instance's health check will pass successfully
# (health check configured at the target group):
# This gets the IP address of the host machine in ECS container env
# https://medium.com/django-unleashed/djangos-allowed-hosts-in-aws-ecs-369959f2c2ab
# from socket import gethostbyname
# from socket import gethostname
# ALLOWED_HOSTS.append(gethostbyname(gethostname()))

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
# SESSION_COOKIE_SECURE = True  # TODO: AW - uncomment this once you have enabled HTTPS
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-name
# SESSION_COOKIE_NAME = "__Secure-sessionid"  # TODO: AW - uncomment this once you have enabled HTTPS
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
# CSRF_COOKIE_SECURE = True  # TODO: AW - uncomment this once you have enabled HTTPS
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-name
# CSRF_COOKIE_NAME = "__Secure-csrftoken"  # TODO: AW - uncomment this once you have enabled HTTPS
# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
# TODO: set this to 60 seconds first and then to 518400 once you prove the former works
SECURE_HSTS_SECONDS = 60
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)

# django-storages s3 backend
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
# ------------------------------------------------------------------------------
# use IAM role instead of AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
_AWS_EXPIRY = 60 * 60 * 24 * 7
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate",
}
AWS_S3_MAX_MEMORY_SIZE = env.int(
    "DJANGO_AWS_S3_MAX_MEMORY_SIZE",
    default=100_000_000,  # 100MB
)
AWS_S3_REGION_NAME = env("DJANGO_AWS_S3_REGION_NAME", default=None)
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#cloudfront
AWS_S3_CUSTOM_DOMAIN = env("DJANGO_AWS_S3_CUSTOM_DOMAIN", default=None)
aws_s3_domain = AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# STATIC & MEDIA
# ------------------------
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "media",
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "static",
            # "default_acl": "public-read",
        },
    },
}
MEDIA_URL = f"https://{aws_s3_domain}/media/"
COLLECTFASTA_STRATEGY = "collectfasta.strategies.boto3.Boto3Strategy"
STATIC_URL = f"https://{aws_s3_domain}/static/"

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="OAC Operations <oacops@cdlib.org>",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    default="[OAC] ",
)
ACCOUNT_EMAIL_SUBJECT_PREFIX = EMAIL_SUBJECT_PREFIX

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL regex.
ADMIN_URL = env("DJANGO_ADMIN_URL")

# Collectfasta
# ------------------------------------------------------------------------------
# https://github.com/jasongi/collectfasta#installation
INSTALLED_APPS = ["collectfasta", *INSTALLED_APPS]

# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        # Errors logged by the SDK itself
        "sentry_sdk": {"level": "ERROR", "handlers": ["console"], "propagate": False},
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

# Sentry
# ------------------------------------------------------------------------------
# SENTRY_DSN = env("SENTRY_DSN")
# SENTRY_LOG_LEVEL = env.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)

# sentry_logging = LoggingIntegration(
#     level=SENTRY_LOG_LEVEL,  # Capture info and above as breadcrumbs
#     event_level=logging.ERROR,  # Send errors as events
# )
# integrations = [sentry_logging, DjangoIntegration()]
# sentry_sdk.init(
#     dsn=SENTRY_DSN,
#     integrations=integrations,
#     environment=env("SENTRY_ENVIRONMENT", default="production"),
#     traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
# )


# Your stuff...
# ------------------------------------------------------------------------------
