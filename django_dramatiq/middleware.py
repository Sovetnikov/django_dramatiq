import json
import logging
import os
import socket
import threading
import time

import psutil
from django import db
from django.db.models import Q
from dramatiq.middleware import Middleware

from django_dramatiq.utils import DateDecimalJSONEncoder

LOGGER = logging.getLogger("django_dramatiq.AdminMiddleware")

# Workers can have multiple threads, but each thread has only one task at a time
_actor_measurement = threading.local()


class AdminMiddleware(Middleware):
    """This middleware keeps track of task executions.
    """

    def after_enqueue(self, broker, message, delay):
        from .models import Task

        LOGGER.debug("Creating Task from message %r.", message.message_id)
        status = Task.STATUS_ENQUEUED
        if delay:
            status = Task.STATUS_DELAYED

        Task.tasks.create_or_update_from_message(message, status=status, actor_name=message.actor_name, queue_name=message.queue_name)

    def before_process_message(self, broker, message):
        from .models import Task

        LOGGER.debug("Updating Task from message %r.", message.message_id)
        hostname = socket.gethostname()
        self._create_or_update_from_message(message, status=Task.STATUS_RUNNING, worker_hostname=hostname)
        _actor_measurement.current_message_id = message.message_id
        _actor_measurement.start = time.monotonic()
        _actor_measurement.start_memory = self._get_memory()

    def after_skip_message(self, broker, message):
        from .models import Task
        # Task can have more than one status - i.e. task failed, then placed in queue again, then skipped
        # skipped status can hide error status
        self.after_process_message(broker, message, task_status=Task.STATUS_SKIPPED)

    def after_process_message(self, broker, message, *, result=None, exception=None, task_status=None):
        try:
            from .models import Task

            status = task_status
            if status is None:
                status = Task.STATUS_DONE
                if exception is not None:
                    status = Task.STATUS_FAILED

            LOGGER.debug("Updating Task from message %r.", message.message_id)
            # Temporary check
            runtime = None
            memory = None
            if _actor_measurement.current_message_id == message.message_id:
                runtime = time.monotonic() - _actor_measurement.start
                memory = round((self._get_memory() - _actor_measurement.start_memory)/1024, 0)
            else:
                # We can get here if other middleware failed in before_process_message handler
                if not exception:
                    LOGGER.error("_actor_measurement.current_message_id (%r) != message.message_id (%r)", _actor_measurement.current_message_id, message.message_id)
            self._create_or_update_from_message(message, status=status, runtime=runtime, memory=memory)
        finally:
            _actor_measurement.current_message_id = None
            _actor_measurement.start = None
            _actor_measurement.start_memory = None

    @classmethod
    def _create_or_update_from_message(self, message, status, **kwargs):
        from .models import Task
        fields = dict(status=status,
                      actor_name=message.actor_name,
                      queue_name=message.queue_name,
                      args=json.dumps(message.args, cls=DateDecimalJSONEncoder, separators=(',', ':')) if message.args else None,
                      kwargs=json.dumps(message.kwargs, cls=DateDecimalJSONEncoder, separators=(',', ':')) if message.kwargs else None, )
        kwargs.update(fields)
        if status == Task.STATUS_SKIPPED:
            # Update task only if task not in DONE or FAILED statuses
            Task.tasks.update_by_filter_from_message(message, filter=~Q(status__in=(Task.STATUS_DONE, Task.STATUS_FAILED)), **kwargs)
        else:
            Task.tasks.create_or_update_from_message(message, **kwargs)

    @classmethod
    def _get_memory(cls):
        process = psutil.Process(os.getpid())
        return process.memory_info().rss


class DbConnectionsMiddleware(Middleware):
    """This middleware cleans up db connections on worker shutdown.
    """

    def _close_old_connections(self, *args, **kwargs):
        db.close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        db.connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections
