import pytest

from .factories import TransactionFactory, ClientFactory, OrderFactory, UserFactory


@pytest.fixture
def transaction(request):
    t = TransactionFactory.create()
    t.order = OrderFactory.create(state='pending')
    t.save()
    return t


@pytest.fixture
def order(request):
    return OrderFactory.create()


@pytest.fixture
def failed_order(request):
    return OrderFactory.create(state='failure')


@pytest.fixture
def pending_order(request, order):
    order.start_pay()
    order.save()
    return order


@pytest.fixture
def cancelled_order(request):
    return OrderFactory.create(state='cancelled')


@pytest.fixture
def transaction_pending(request, pending_order):
    o = OrderFactory.create(state='pending', transaction__status='pending')
    return o.transaction


@pytest.fixture
def gutsclient(request):
    return ClientFactory.create(name='guts', secret='ihaveguts')


@pytest.fixture
def ideal_transaction(request, transaction):
    transaction.payment_method = 'ideal'
    transaction.order.total = 25.0
    transaction.bank_code = "ABNANL2A"
    return transaction


@pytest.fixture
def cc_transaction(request, transaction):
    transaction.payment_method = 'creditcard'
    transaction.order.total = 50.0
    transaction.card = "mastercard"
    return transaction


@pytest.fixture
def completed_order(request, pending_order, user):
    pending_order.completed()
    return pending_order


@pytest.fixture
def user(request):
    return UserFactory.create()
