# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-11-15 13:18
from __future__ import unicode_literals

from django.db import migrations, models
import django_fsm
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('buckaroo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('payment_method', models.CharField(choices=[('ideal', 'iDeal'), ('creditcard', 'Creditcard')], max_length=300)),
                ('payment_key', models.CharField(blank=True, max_length=300, null=True)),
                ('transaction_key', models.CharField(blank=True, max_length=300, null=True)),
                ('refunded', models.BooleanField(default=False)),
                ('status', django_fsm.FSMField(default='new', max_length=50, protected=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('redirect_url', models.CharField(blank=True, max_length=500, null=True)),
                ('card', models.CharField(blank=True, max_length=100, null=True)),
                ('bank_code', models.CharField(blank=True, max_length=100, null=True)),
                ('last_push', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
