# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-03 14:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('infoextr', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='Dcestination',
            new_name='Destination',
        ),
    ]