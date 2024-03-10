from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SmartThrift.settings')

app = Celery('SmartThrift')
app.conf.enable_utc = False
app.conf.update(timezone = 'Europe/Berlin')
app.config_from_object('django.conf:settings', namespace='CELERY')


# Celery Beat Settings
# celery beat will replace django in sending the task to rabbitmq


app.autodiscover_tasks()
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')