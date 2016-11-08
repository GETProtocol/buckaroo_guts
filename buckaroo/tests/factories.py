import factory
import random

from ..models import Transaction
from order.tests.factories import OrderFactory


def random_string(o):
    return hex(random.getrandbits(80))[2:]


class TransactionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Transaction

    transaction_key = factory.LazyAttribute(random_string)

    order = factory.SubFactory(OrderFactory)
