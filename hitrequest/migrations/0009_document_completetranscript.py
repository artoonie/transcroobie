# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-06 04:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hitrequest', '0008_auto_20161102_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='completeTranscript',
            field=models.TextField(blank=True),
        ),
    ]
