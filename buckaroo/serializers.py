# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Transaction
        fields = ('id', 'payment_method', 'order', 'status', 'uuid',
                  'redirect_url', 'card', 'bank_code')
