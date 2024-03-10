from celery import shared_task
from celery.utils.log import get_task_logger
from .email import send_register_email

logger = get_task_logger(__name__)



@shared_task(name='send_register_email_task')
def send_register_email_task(name, email, category):
    logger.info('Sent Welcome Email')
    return send_register_email(name, email, category)