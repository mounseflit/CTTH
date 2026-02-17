"""Celery app stub — Celery is no longer required to run the core app.

Tasks have been converted to plain functions in data_tasks.py and report_tasks.py.
They are called via FastAPI BackgroundTasks / run_in_executor instead.

If you want to re-enable Celery later, uncomment the block below and add
CELERY_BROKER_URL / CELERY_RESULT_BACKEND to your .env and Settings model.
"""

# from celery import Celery
# from celery.schedules import crontab
# from app.config import settings
#
# celery_app = Celery(
#     "ctth_tasks",
#     broker=settings.CELERY_BROKER_URL,
#     backend=settings.CELERY_RESULT_BACKEND,
#     include=["app.tasks.data_tasks", "app.tasks.report_tasks"],
# )
