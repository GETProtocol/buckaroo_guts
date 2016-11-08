import pytest

from .factories import TransactionFactory


@pytest.fixture
def transaction(request):
    return TransactionFactory.create(order__state='pending')


@pytest.fixture
def transaction_pending(request):
    return TransactionFactory.create(status='pending',
                                     order__state='pending')


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
def buckaroo_settings(request, settings):
    settings.BUCKAROO_WEBSITE_KEY = '12345'
    settings.BUCKAROO_SECRET_KEY = '54321'
    settings.BUCKAROO_CHECKOUT_URL = 'notrelevant'
    return settings


@pytest.fixture
def no_website_settings(request, settings):
    del settings.BUCKAROO_WEBSITE_KEY
    settings.BUCKAROO_SECRET_KEY = '54321'
    settings.BUCKAROO_CHECKOUT_URL = 'notrelevant'
    return settings


@pytest.fixture
def no_secret_settings(request, settings):
    del settings.BUCKAROO_SECRET_KEY
    settings.BUCKAROO_WEBSITE_KEY = '12345'
    settings.BUCKAROO_CHECKOUT_URL = 'notrelevant'
    return settings


@pytest.fixture
def no_checkout_settings(request, settings):
    del settings.BUCKAROO_CHECKOUT_URL
    settings.BUCKAROO_WEBSITE_KEY = '12345'
    settings.BUCKAROO_SECRET_KEY = '54321'
    return settings


@pytest.fixture
def no_buckaroo_settings(request, settings):
    del settings.BUCKAROO_WEBSITE_KEY
    del settings.BUCKAROO_SECRET_KEY
    del settings.BUCKAROO_CHECKOUT_URL
    return settings
