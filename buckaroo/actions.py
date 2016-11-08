from decimal import Decimal
from django.conf import settings
from rest_framework import status

from actstream import action

from .exceptions import BuckarooException
from .models import (BUCKAROO_790_PENDING_INPUT, BUCKAROO_791_PENDING_PROCESSING,
                     BUCKAROO_792_AWAITING_CONSUMER, BUCKAROO_190_SUCCESS,
                     BUCKAROO_793_ON_HOLD)

from .utils import (construct_url, buckaroo_api_call, get_base_transaction_json,
                    add_pay_json, add_ideal_json, get_payment_key, get_transaction_key,
                    get_redirect_url, get_buckaroo_status_code, add_refund_json,
                    add_creditcard_json, verify_transaction_fields)


import logging
logger = logging.getLogger(__name__)


BUCKAROO_PENDING_STATUSES = [BUCKAROO_790_PENDING_INPUT,
                             BUCKAROO_791_PENDING_PROCESSING,
                             BUCKAROO_792_AWAITING_CONSUMER]


BUCKAROO_BASE_TEST_URL = 'https://testcheckout.buckaroo.nl/'
BUCKAROO_BASE_PRODUCTION_URL = 'https://checkout.buckaroo.nl/'

BUCKAROO_CHECKOUT_URL = "json/Transaction/"
BUCKAROO_REFUND_URL = 'json/Transaction/RefundInfo/'

BANK_CODES = (
    ('ABNANL2A', 'ABN AMRO'),
    ('ASNBNL21', 'ASN Bank'),
    ('INGBNL2A', 'ING'),
    ('RABONL2U', 'Rabobank'),
    ('SNSBNL2A', 'SNS Bank'),
    ('RBRBNL21', 'RegioBank'),
    ('TRIONL2U', 'Triodos Bank'),
    ('FVLBNL22', 'Van Lanschot'),
    ('KNABNL2H', 'Knab bank'),
    ('BUNQNL2A', 'Bunq')
)


class BuckarooSettingsMixin:

    def __init__(self):
        try:
            assert settings.BUCKAROO_CHECKOUT_URL
        except AttributeError:
            raise BuckarooException("BUCKAROO_CHECKOUT_URL settings missing")

        try:
            assert settings.BUCKAROO_WEBSITE_KEY
        except AttributeError:
            raise BuckarooException("BUCKAROO_WEBSITE_KEY setting missing")

        try:
            assert settings.BUCKAROO_SECRET_KEY
        except AttributeError:
            raise BuckarooException("BUCKAROO_SECRET_KEY setting missing")


class Pay(BuckarooSettingsMixin):

    def __init__(self, transaction=None, testing=None):

        super().__init__()

        self.transaction = transaction
        self.testing = testing

    def pay(self):

        verify_transaction_fields(transaction=self.transaction)

        data = self._prepare_pay_json()

        url = construct_url()

        res = buckaroo_api_call(self.transaction, url, "POST", data)

        self._handle_transaction_response(response=res)

    def _prepare_pay_json(self):
        base = get_base_transaction_json(self.transaction)
        body = add_pay_json(base, self.transaction)

        if self.transaction.payment_method == 'ideal':
            return add_ideal_json(body, self.transaction, 'pay')
        elif self.transaction.payment_method == 'creditcard':
            return add_creditcard_json(body, self.transaction, 'pay')
        else:
            return {}

    def _handle_transaction_response(self, response=None):
        """Handle the Buckaroo response to update the transaction."""

        self.transaction.payment_key = get_payment_key(response.json())
        self.transaction.save()

        self.transaction.transaction_key = get_transaction_key(response.json())
        self.transaction.save()

        if response.status_code != status.HTTP_200_OK:
            raise BuckarooException({"message": 'Invalid API status code',
                                     "description": "The request to the Buckaroo API was "
                                     "unsuccessful",
                                     "status": response.status_code})

        b_status_code = get_buckaroo_status_code(response.json())

        if b_status_code not in BUCKAROO_PENDING_STATUSES:
            raise BuckarooException({"message": "Invalid Buckaroo transaction status",
                                     "Buckaroo Status": b_status_code})

        self.transaction.pending()
        self.transaction.redirect_url = get_redirect_url(response.json())
        self.transaction.save()


class Refund(BuckarooSettingsMixin):
    """Refunding happens on a per ticket basis."""

    def __init__(self, transaction=None, amount=0, testing=True):

        super().__init__()

        self.transaction = transaction
        self.testing = testing
        self.fee = Decimal(settings.BUCKAROO_REFUND_FEE)
        self.amount = amount
        self.refund_amount = self.amount - self.fee

        # No fee if fee larger than amount (e.g. with test transactions)
        if self.refund_amount < 0:
            self.refund_amount = self.amount

        if self.testing:
            self.refund_info_url = ''.join([BUCKAROO_BASE_TEST_URL,
                                            BUCKAROO_REFUND_URL])
        else:
            self.refund_info_url = ''.join([BUCKAROO_BASE_PRODUCTION_URL,
                                            BUCKAROO_REFUND_URL])

        self.is_refundable = False
        self.max_refund_amount = -1
        self.partial_allowed = False
        self.refunded_amount = 0

    def _update_refund_info(self, response={}):
        try:
            self.is_refundable = response['IsRefundable']
        except KeyError:
            logger.error("'IsRefundable' key not found in API response")
            raise BuckarooException(
                {"message": "'IsRefundable' key not in API response"})

        try:
            self.max_refund_amount = response['MaximumRefundAmount']
        except KeyError:
            logger.error("'MaximumRefundAmount' key not found in API response")
            raise BuckarooException(
                {"message": "'MaximumRefundAmount' not in API response"})

        try:
            self.partial_allowed = response['AllowPartialRefund']
        except KeyError:
            logger.error("'AllowPartialRefund' key not found in API response")
            raise BuckarooException(
                {"message": "'AllowPartialRefund' not in API response"})

        try:
            self.refunded_amount = response['RefundedAmount']
        except KeyError:
            logger.error("'RefundedAmonut' key not found in API response")
            raise BuckarooException(
                {"message": "'RefundedAmonut' not in API response"})

    def get_refund_info(self):
        """Get the refund options for a transaction."""
        url = ''.join([self.refund_info_url, str(
            self.transaction.transaction_key)])

        res = buckaroo_api_call(self.transaction, url, 'GET')

        self._update_refund_info(response=res.json())

    def _prepare_refund_json(self):

        base = get_base_transaction_json(self.transaction)
        body = add_refund_json(base, self.transaction, self.refund_amount)

        if self.transaction.payment_method == 'ideal':
            return add_ideal_json(body, self.transaction, 'refund')
        elif self.transaction.payment_method == 'creditcard':
            return add_creditcard_json(body, self.transaction, 'refund')
        return {}

    def refund(self):
        if settings.BUCKAROO_DISABLE_REFUND:
            return

        self.get_refund_info()

        if not self.partial_allowed or not (self.amount - self.fee) <= self.max_refund_amount:
            logger.error("Unable to refund. Ticket price too high to refund")
            raise BuckarooException({"message": 'Ticket price too high'})

        data = self._prepare_refund_json()

        url = construct_url()

        res = buckaroo_api_call(self.transaction, url, "POST", data)

        self._handle_transaction_response(response=res)

    def _handle_transaction_response(self, response=None):
        """Handle the Buckaroo response to update the transaction."""
        if response.status_code != status.HTTP_200_OK:
            raise BuckarooException({"message": 'Invalid API status code',
                                     "description": "The request to the Buckaroo API was "
                                     "unsuccessful",
                                     "status": response.status_code})

        b_status_code = get_buckaroo_status_code(response.json())

        if b_status_code == BUCKAROO_190_SUCCESS:
            self.transaction.refunded = True
            self.transaction.save()
            action.send(self.transaction, verb="was refunded (190, immediate)")
            logger.info("Transaction {0} successfully refunded"
                        .format(self.transaction.transaction_key))
        elif b_status_code == BUCKAROO_793_ON_HOLD:
            self.transaction.refunded = True
            self.transaction.save()
            action.send(self.transaction, verb="was refunded (793, on hold)")
            logger.info("Transaction {0} successfully refunded (but ONHOLD)"
                        .format(self.transaction.transaction_key))

        else:
            logger.error("Something went wrong with the Refund transaction")
            logger.error("{0}".format(response.json()))
            raise BuckarooException({"message": "Invalid Buckaroo transaction status",
                                     "Buckaroo Status": b_status_code})
