import pytest
import hashlib
import urllib.parse

from django.core.urlresolvers import reverse
from rest_framework import status

from buckaroo.views import update_transaction
from .factories import OrderFactory
from ..models import (BUCKAROO_190_SUCCESS, BUCKAROO_890_CANCELLED_BY_USER,
                      BUCKAROO_490_FAILED,
                      BUCKAROO_790_PENDING_INPUT, BUCKAROO_690_REJECTED,
                      Transaction)
from .factories import TransactionFactory
from buckaroo.utils import update_transaction_post


class Response:

    def __init__(self,
                 status_code=None,
                 PaymentKey=1235,
                 Key=54321,
                 Status=None,
                 RequiredAction=None):
        self.status_code = status_code
        self.PaymentKey = PaymentKey
        self.Key = Key
        self.Status = Status
        self.RequiredAction = RequiredAction

    def json(self):
        return self

    def __getitem__(self, item):
        return getattr(self, item)


@pytest.mark.django_db(transaction=False)
class TestUpdateTransaction:

    def test_no_transaction(self):
        res = update_transaction(data=1)
        assert res is None

    def test_no_data(self):
        res = update_transaction(transaction=1)
        assert res is None

    def test_update_no_code(self):
        o = OrderFactory.create(state='pending')
        t = TransactionFactory.create()
        t.order = o
        t.save()

        data = {1: 1}

        assert t.last_push is None

        update_transaction(transaction=t, data=data)

        assert t.status == t.STATUS_NEW
        assert t.last_push is not None

    def test_status_update_success(self):
        o = OrderFactory.create(state='pending')
        t = TransactionFactory.create(status='pending')
        t.order = o
        t.save()

        data = dict(Status=dict(Code=dict(Code=BUCKAROO_190_SUCCESS)))

        update_transaction(transaction=t, data=data)

        assert t.status == t.STATUS_SUCCESS
        assert t.last_push is not None

    def test_status_update_cancelled(self):
        o = OrderFactory.create(state='pending')
        t = TransactionFactory.create(status='pending')
        t.order = o
        t.save()

        data = dict(Status=dict(
            Code=dict(Code=BUCKAROO_890_CANCELLED_BY_USER)))

        update_transaction(transaction=t, data=data)

        assert t.status == t.STATUS_CANCELLED

    def test_status_update_failed(self):
        o = OrderFactory.create(state='pending')
        t = TransactionFactory.create(status='pending')
        t.order = o
        t.save()

        data = dict(Status=dict(Code=dict(Code=BUCKAROO_490_FAILED)))

        update_transaction(transaction=t, data=data)

        assert t.status == t.STATUS_FAILED

    def test_status_update_rejected(self):
        o = OrderFactory.create(state='pending')
        t = TransactionFactory.create(status='pending')
        t.order = o
        t.save()

        data = dict(Status=dict(Code=dict(Code=BUCKAROO_690_REJECTED)))

        update_transaction(transaction=t, data=data)

        assert t.status == t.STATUS_REJECTED


@pytest.fixture
def simple_data(request):
    return {'BRQ_TRANSACTIONS': '4ED2032582DF418BADF21587BE406453'}


@pytest.mark.django_db(transaction=False)
class TestTransactionUpdate:

    def test_update_transaction_success(self, simple_data, pending_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_190_SUCCESS
        o = OrderFactory.create(state='pending',
                                transaction__status='pending',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = pending_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_transaction_already_success(self, simple_data, completed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_190_SUCCESS
        o = OrderFactory.create(state='completed',
                                transaction__status='success',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = completed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_new_transaction_to_success(self, simple_data, order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_190_SUCCESS
        o = OrderFactory.create(transaction__status='new',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'new'
        assert t.order.state == 'created'

    def test_update_transaction_cancelled(self, simple_data, pending_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_890_CANCELLED_BY_USER
        o = OrderFactory.create(state='pending',
                                transaction__status='pending',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = pending_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'cancelled'
        assert t.order.state == 'cancelled'

    def test_update_transaction_already_cancelled(self, simple_data, cancelled_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_890_CANCELLED_BY_USER
        o = OrderFactory.create(state='cancelled',
                                      transaction__status='cancelled',
                                      transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = cancelled_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'cancelled'
        assert t.order.state == 'cancelled'

    def test_update_new_transaction_to_cancelled(self, simple_data, order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_890_CANCELLED_BY_USER
        o = OrderFactory.create(transaction__status='new',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'new'
        assert t.order.state == 'created'

    def test_update_success_transaction_to_cancelled(self, simple_data, completed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_890_CANCELLED_BY_USER
        o = OrderFactory.create(state='completed',
                                transaction__status='success',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')

        # t.order = completed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_transaction_pending(self, simple_data, order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_790_PENDING_INPUT
        o = OrderFactory.create(transaction__status='new',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'pending'
        assert t.order.state == 'created'  # Transaction doesn't change order to pending

    def test_update_transaction_already_pending(self, simple_data, pending_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_790_PENDING_INPUT
        o = OrderFactory.create(state='pending',
                                transaction__status='pending',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = pending_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'pending'
        assert t.order.state == 'pending'

    def test_update_success_transaction_to_pending(self, simple_data, completed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_790_PENDING_INPUT
        o = OrderFactory.create(state='completed',
                                transaction__status='success',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = completed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_transaction_rejected(self, simple_data, pending_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_690_REJECTED
        t = OrderFactory.create(state='pending',
                                      transaction__status='pending',
                                      transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = pending_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'rejected'
        assert t.order.state == 'failure'

    def test_update_transaction_already_rejected(self, simple_data, failed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_690_REJECTED
        t = OrderFactory.create(state='failure',
                                      transaction__status='rejected',
                                      transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = failed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'rejected'
        assert t.order.state == 'failure'

    def test_update_new_transaction_to_rejected(self, simple_data, order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_690_REJECTED
        o = OrderFactory.create(transaction__status='new',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'new'
        assert t.order.state == 'created'

    def test_update_success_transaction_to_rejected(self, simple_data, completed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_690_REJECTED
        o = OrderFactory.create(state='completed',
                                transaction__status='success',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = completed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_transaction_failed(self, simple_data, pending_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_490_FAILED
        o = OrderFactory.create(state='pending',
                                      transaction__status='pending',
                                      transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = pending_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'failed'
        assert t.order.state == 'failure'

    def test_update_transaction_already_failed(self, simple_data, failed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_490_FAILED
        o = OrderFactory.create(state='failure',
                                      transaction__status='failed',
                                      transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = failed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'failed'
        assert t.order.state == 'failure'

    def test_update_new_transaction_to_failed(self, simple_data, order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_490_FAILED

        o = OrderFactory.create(transaction__status='new',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453')
        # t.order = order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'new'
        assert t.order.state == 'created'

    def test_update_success_transaction_to_failed(self, simple_data, completed_order):
        simple_data['BRQ_STATUSCODE'] = BUCKAROO_490_FAILED
        o = OrderFactory.create(state='completed',
                                transaction__status='success',
                                transaction__transaction_key='4ED2032582DF418BADF21587BE406453') 
        # t.order = completed_order
        # t.save()

        update_transaction_post(data=simple_data)

        t = Transaction.objects.get(
            transaction_key='4ED2032582DF418BADF21587BE406453')

        assert t.status == 'success'
        assert t.order.state == 'completed'

    def test_update_transaction_not_found(self, simple_data, gutsclient):
        TransactionFactory.create(payment_key='DOESNOTEXIST')

        assert update_transaction_post(data=simple_data) is None


@pytest.mark.django_db(transaction=False)
class TestRedirectView:
    """Test redirect from Buckaroo POST push to our Ember server."""

    def test_invalid_signature(self, client, gutsclient):
        print(gutsclient.id)
        response = client.post(
            reverse('guts_payment_return', kwargs={'pk': 1}), {})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_success(self, client, transaction_pending, gutsclient):
        data = dict(BRQ_STATUSCODE=BUCKAROO_190_SUCCESS,
                    BRQ_TRANSACTIONS=transaction_pending.transaction_key)
        dataenc = "".join("{}={}".format(k, v) for (k, v) in sorted(
            data.items())) + gutsclient.secret
        sig = hashlib.sha1(dataenc.encode('utf8')).hexdigest()
        data["BRQ_SIGNATURE"] = sig

        response = client.post(
            reverse('guts_payment_return',
                    kwargs={'pk': transaction_pending.order.id}), data=data)
        assert response.status_code == status.HTTP_302_FOUND

        args = dict(urllib.parse.parse_qsl(
            response['location'].rsplit('/', 1)[-1]))
        assert args['flag'] == 'success'
        # assert int(
        #     args['event']) == transaction_pending.order.tickets.first().event_id

    def test_cancelled(self, client, transaction_pending, gutsclient):
        data = dict(BRQ_STATUSCODE=BUCKAROO_890_CANCELLED_BY_USER,
                    BRQ_TRANSACTIONS=transaction_pending.transaction_key)
        dataenc = "".join("{}={}".format(k, v) for (k, v) in sorted(
            data.items())) + gutsclient.secret
        sig = hashlib.sha1(dataenc.encode('utf8')).hexdigest()
        data["BRQ_SIGNATURE"] = sig

        response = client.post(
            reverse('guts_payment_return',
                    kwargs={'pk': transaction_pending.order.id}), data=data)
        assert response.status_code == status.HTTP_302_FOUND

        args = dict(urllib.parse.parse_qsl(
            response['location'].rsplit('/', 1)[-1]))
        assert args['flag'] == 'cancelled'
        # assert int(
        #     args['event']) == transaction_pending.order.tickets.first().event_id

    def test_failure(self, client, transaction_pending, gutsclient):
        print("NOOOOO", transaction_pending.order)
        data = dict(BRQ_STATUSCODE=BUCKAROO_490_FAILED,
                    BRQ_TRANSACTIONS=transaction_pending.transaction_key)
        dataenc = "".join("{}={}".format(k, v) for (k, v) in sorted(
            data.items())) + gutsclient.secret
        sig = hashlib.sha1(dataenc.encode('utf8')).hexdigest()
        data["BRQ_SIGNATURE"] = sig

        response = client.post(
            reverse('guts_payment_return',
                    kwargs={'pk': transaction_pending.order.id}), data=data)
        assert response.status_code == status.HTTP_302_FOUND

        args = dict(urllib.parse.parse_qsl(
            response['location'].rsplit('/', 1)[-1]))
        assert args['flag'] == 'failed'
        # assert int(
        #     args['event']) == transaction_pending.order.tickets.first().event_id
