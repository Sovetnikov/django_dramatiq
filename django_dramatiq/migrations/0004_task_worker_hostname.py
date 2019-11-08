# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0003_task_runtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='worker_hostname',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
