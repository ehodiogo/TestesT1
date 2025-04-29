import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Projeto.settings")

app = Celery("Projeto")

app.conf.update(
    broker_url='redis://redis:6379/0',     
    result_backend='redis://redis:6379/0',  
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    result_persistent=True,
    task_reject_on_worker_lost=True,
    timezone="America/Sao_Paulo",
    task_acks_late=True,
    task_track_started=True,
)

app.autodiscover_tasks()

import redis
r = redis.Redis(host='redis', port=6379, db=0)
print(r.ping())  # Deve retornar True se a conexão estiver funcionando
