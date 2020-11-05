# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0006_task_memory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='memory',
            field=models.IntegerField(verbose_name='process memory delta', null=True, help_text='in bytes'),
        ),
    ]
