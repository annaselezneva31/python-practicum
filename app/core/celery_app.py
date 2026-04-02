from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "facts",
    broker=settings.celery_broker_url, # where Celery sends tasks
    backend=settings.celery_result_backend # where results are stored
)

celery_app.conf.update(
    beat_schedule={
        "run-me-every-20-seconds": {
            "task": "app.tasks.facts.fetch_and_store_fact",
            "schedule": settings.fetch_interval_seconds,
            "args": (),
        }
    },
    timezone="UTC"
)

# where to look for tasks
celery_app.autodiscover_tasks(["app.tasks"])