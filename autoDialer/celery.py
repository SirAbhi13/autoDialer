import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoDialer.settings")

app = Celery("autoDialer")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.loader.override_backends["django-db"] = (
    "django_celery_results.backends.database:DatabaseBackend"
)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(
    task_track_started=True,
    task_ignore_result=False,
    result_backend="db+sqlite:///django-db",
    #    include=['apps.xxx.tasks',],
)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
