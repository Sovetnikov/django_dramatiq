# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0002_auto_20191104_1354'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='runtime',
            field=models.FloatField(verbose_name='execution time', null=True, help_text='in seconds'),
        ),
    ]
