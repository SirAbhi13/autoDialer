import logging

from celery import shared_task
from celery.result import AsyncResult
from django.conf import settings

from api.services.dialer import TwilioDialerService

logger = logging.getLogger(__name__)


@shared_task
def dial(id, message):
    # try:

    dialer_service = TwilioDialerService(
        getattr(settings, "TWILIO_ACCOUNT_SID"), getattr(settings, "TWILIO_AUTH_TOKEN")
    )

    dialer_service.dialContactList(id, message)

    return True


@shared_task(name="api.tasks.test_task")
def test_task():
    logger.info("Running test task")
    return "Test task completed successfully"


@shared_task(name="api.tasks.debug_result_backend")
def debug_result_backend():
    task_id = debug_result_backend.request.id
    logger.info(f"Debug task ID: {task_id}")
    result = AsyncResult(task_id)
    logger.info(f"Result backend type: {type(result.backend)}")
    logger.info(f"Result backend: {str(result.backend)}")
    return "Debug task completed"
