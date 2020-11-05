# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_dramatiq', '0005_auto_20200207_1208'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='memory',
            field=models.PositiveIntegerField(verbose_name='process memory delta', null=True, help_text='in bytes'),
        ),
    ]
