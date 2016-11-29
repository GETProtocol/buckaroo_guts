import pytest
import uuid
from .factories import OrderFactory
from ..serializers import TransactionSerializer
from ..models import Transaction
from .models import Order


@pytest.mark.django_db(transaction=False)
class TestTransactionSerializer:

    def test_transaction_created(self):
        """
        Assert that the transaction is correctly linked
        to the order when its created
        """

        o = OrderFactory.create(transaction=None)
        assert Transaction.objects.count() == 0

        data = dict(payment_method='ideal',
                    redirect_url='www.test.com',
                    uuid=str(uuid.uuid4()),
                    order=o.id
                    )

        instance = TransactionSerializer(data=data)
        instance.is_valid()
        instance.save()

        o = Order.objects.get(id=o.id)
        assert o.transaction == Transaction.objects.first()
        assert Transaction.objects.count() == 1
