from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.timezone import now
from dramatiq import Message

from .apps import DjangoDramatiqConfig

#: The database label to use when storing task metadata.
DATABASE_LABEL = DjangoDramatiqConfig.tasks_database()


class TaskManager(models.Manager):
    def create_or_update_from_message(self, message, **extra_fields):
        task, _ = self.using(DATABASE_LABEL).update_or_create(
            id=message.message_id,
            defaults={
                "message_data": message.encode(),
                **extra_fields,
            }
        )
        return task

    def update_by_filter_from_message(self, message, filter, **extra_fields):
        self.using(DATABASE_LABEL).filter(Q(id=message.message_id) & filter).update(**extra_fields)

    def delete_old_tasks(self, max_task_age):
        self.using(DATABASE_LABEL).filter(
            created_at__lte=now() - timedelta(seconds=max_task_age)
        ).delete()


class Task(models.Model):
    STATUS_ENQUEUED = "enqueued"
    STATUS_DELAYED = "delayed"
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"
    STATUS_DONE = "done"
    STATUS_SKIPPED = "skipped"
    STATUSES = [
        (STATUS_ENQUEUED, "Enqueued"),
        (STATUS_DELAYED, "Delayed"),
        (STATUS_RUNNING, "Running"),
        (STATUS_FAILED, "Failed"),
        (STATUS_DONE, "Done"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, editable=False)
    status = models.CharField(max_length=8, choices=STATUSES, default=STATUS_ENQUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    message_data = models.BinaryField()

    actor_name = models.CharField(max_length=300, null=True)
    queue_name = models.CharField(max_length=100, null=True)
    runtime = models.FloatField(verbose_name='execution time', null=True, help_text='in seconds')
    worker_hostname = models.CharField(max_length=300, null=True)
    args = models.TextField(verbose_name='Arguments', null=True)
    kwargs = models.TextField(verbose_name='Keyword arguments', null=True)
    memory = models.IntegerField(verbose_name='process memory delta', null=True, help_text='in kb')

    tasks = TaskManager()

    class Meta:
        ordering = ["-updated_at"]

    @cached_property
    def message(self):
        return Message.decode(bytes(self.message_data))

    def __str__(self):
        msg_str = str(self.message)
        return (msg_str[:150] + '..') if len(msg_str) > 150 else msg_str

