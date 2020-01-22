import logging
import socket
import threading
import time

from django import db
from dramatiq.middleware import Middleware

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
        Task.tasks.create_or_update_from_message(message, status=Task.STATUS_RUNNING, actor_name=message.actor_name, queue_name=message.queue_name, worker_hostname=hostname)
        _actor_measurement.current_message_id = message.message_id
        _actor_measurement.start = time.monotonic()

    def after_skip_message(self, broker, message):
        from .models import Task
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
            if _actor_measurement.current_message_id != message.message_id:
                raise Exception('_actor_measurement.current_message_id != message.message_id')
            runtime = time.monotonic() - _actor_measurement.start
            Task.tasks.create_or_update_from_message(message, status=status, actor_name=message.actor_name, queue_name=message.queue_name, runtime=runtime)
        finally:
            _actor_measurement.current_message_id = None
            _actor_measurement.start = None


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
