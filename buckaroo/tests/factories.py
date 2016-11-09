import factory
import random

from django.contrib.auth.models import User

from ..models import Transaction
from .models import Order


def random_string(o):
    return hex(random.getrandbits(80))[2:]


class UserFactory(factory.DjangoModelFactory):

    class Meta:
        model = User

    username = factory.LazyAttribute(lambda o: '{0}.{1}{2}'.format(
        o.first_name, o.last_name, random.choice(range(1000))).lower())
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class OrderFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Order

    owner = factory.SubFactory(UserFactory)


class TransactionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Transaction

    transaction_key = factory.LazyAttribute(random_string)

    order = factory.SubFactory(OrderFactory)
