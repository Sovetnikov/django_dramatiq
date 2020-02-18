import decimal
import json
import math
from datetime import datetime

from django.conf import settings
from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_dramatiq.humanize import naturaldate
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    exclude = ("message_data", "runtime")
    readonly_fields = ("message_details", "traceback", "status", "queue_name", "actor_name", "runtime_display", "worker_hostname", "result", "args", "kwargs")
    list_display = (
        "__str__",
        "status",
        "eta",
        "created_at",
        "updated_at",
        "queue_name",
        "actor_name",
        "runtime_display",
        "worker_hostname",
    )
    list_filter = ("status", "created_at", "queue_name", "actor_name", "worker_hostname")
    search_fields = ("actor_name", "args", "kwargs")

    def eta(self, instance):
        timestamp = (
                instance.message.options.get("eta", instance.message.message_timestamp) / 1000
        )

        # Django expects a timezone-aware datetime if USE_TZ is True, and a naive datetime in localtime otherwise.
        tz = timezone.utc if settings.USE_TZ else None
        return naturaldate(datetime.fromtimestamp(timestamp, tz=tz))

    def message_details(self, instance):
        message_details = json.dumps(instance.message._asdict(), indent=4)
        return mark_safe("<pre>%s</pre>" % message_details)

    def traceback(self, instance):
        traceback = instance.message.options.get("traceback", None)
        if traceback:
            return mark_safe("<pre>%s</pre>" % traceback)
        return None

    def result(self, instance):
        if instance.status == Task.STATUS_DONE:
            try:
                result = instance.message.get_result(timeout=50)  # timeout in ms
                return mark_safe("<pre>%s</pre>" % str(result)[0:2000] if result is not None else 'None')
            except Exception as e:
                return str(e)
        return ''

    def runtime_display(self, instance):
        if instance.runtime is None:
            return None
        precision = None
        if instance.runtime < 1:
            # Display last digit after decimal point
            return '%s sec' % round(decimal.Decimal(instance.runtime), abs(int(math.log10(abs(instance.runtime)))) + 1)
        elif instance.runtime < 10:
            precision = 1
        return '%s sec' % round(instance.runtime, precision)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, task=None):
        return False

    def has_delete_permission(self, request, task=None):
        return False
