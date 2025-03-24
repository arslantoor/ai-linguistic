"""Celery configuration for white_label."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
app = Celery("white_label")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
