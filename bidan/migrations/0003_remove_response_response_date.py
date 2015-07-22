# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bidan', '0002_auto_20150507_1617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='response',
            name='response_date',
        ),
    ]
