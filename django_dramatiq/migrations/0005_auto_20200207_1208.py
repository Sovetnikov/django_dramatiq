# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0004_task_worker_hostname'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='args',
            field=models.TextField(verbose_name='Arguments', null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='kwargs',
            field=models.TextField(verbose_name='Keyword arguments', null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(max_length=8, default='enqueued', choices=[('enqueued', 'Enqueued'), ('delayed', 'Delayed'), ('running', 'Running'), ('failed', 'Failed'), ('done', 'Done'), ('skipped', 'Skipped')]),
        ),
    ]
