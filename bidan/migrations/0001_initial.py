# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response_text', models.TextField()),
                ('response_date', models.DateTimeField(verbose_name=b'date published')),
                ('repsonse_username', models.CharField(max_length=200)),
                ('response_password', models.CharField(max_length=200)),
            ],
        ),
    ]
