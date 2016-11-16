# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import Transaction, ModelResolver

modelresolver = ModelResolver()


class TransactionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(required=False, allow_null=True)
    order = serializers.PrimaryKeyRelatedField(queryset=modelresolver('Order').objects.all())

    class Meta:
        model = Transaction
        fields = ('id', 'payment_method', 'status', 'uuid', 'order',
                  'redirect_url', 'card', 'bank_code')

    def create(self, validated_data):

        order = validated_data.pop('order')
        transaction = Transaction.objects.create(**validated_data)
        transaction.order = order
        transaction.save()
        return transaction
