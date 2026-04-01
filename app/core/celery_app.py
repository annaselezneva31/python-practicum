from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "facts",
    ...
)

celery_app.conf.update(
    ...
)
