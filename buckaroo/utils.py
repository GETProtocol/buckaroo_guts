"""Set of helpers for Buckaroo API."""

import hashlib
import urllib.parse
import logging
import requests

from collections import OrderedDict

from django.core.urlresolvers import reverse

from django_fsm import TransitionNotAllowed
from .models import Transaction
from .exceptions import BuckarooException
from .auth import AuthHeader

logger = logging.getLogger(__name__)


def get_transaction_from_response(data=None):
    transaction_key = data.get('BRQ_TRANSACTIONS', None)

    if not transaction_key:
        logger.error("Transaction key not found in Buckaroo POST")
        return

    try:
        transaction = Transaction.objects.get(transaction_key=transaction_key)
    except Transaction.DoesNotExist:
        logger.error("Transaction not found for payment key: {0}".format(transaction_key))
        return
    return transaction


def get_buckaroo_status_from_response(data=None):
        b_status = data.get('BRQ_STATUSCODE')
        if b_status:
            return int(b_status)
        return None


def update_transaction_post(data=None):
    if not data:
        return

    transaction = get_transaction_from_response(data=data)

    buckaroo_status = get_buckaroo_status_from_response(data=data)

    if buckaroo_status:
        transaction_status = transaction.map_status(status_code=buckaroo_status)

        if transaction_status == transaction.STATUS_SUCCESS:
            try:
                transaction.success()
            except TransitionNotAllowed as e:
                logger.exception("Update of transaction to state success failed. {0}".format(e))

        if transaction_status == transaction.STATUS_CANCELLED:
            try:
                transaction.cancelled()
            except TransitionNotAllowed as e:
                logger.exception("Update of transaction to state cancelled failed. {0}".format(e))

        if transaction_status == transaction.STATUS_PENDING:
            try:
                transaction.pending()
            except TransitionNotAllowed as e:
                logger.exception(
                    "Update of transaction to state pending failed. {0}".format(e))

        if transaction_status == transaction.STATUS_REJECTED:
            try:
                transaction.rejected()
            except TransitionNotAllowed as e:
                logger.exception(
                    "Update of transaction to state rejected failed. {0}".format(e))

        if transaction_status == transaction.STATUS_FAILED:
            try:
                transaction.failed()
            except TransitionNotAllowed as e:
                logger.exception(
                    "Update of transaction to state failed failed. {0}".format(e))

        transaction.save()

    return transaction


def verify_buckaroo_signature(data, client):
    buckaroo_signature = data.get('BRQ_SIGNATURE', None)
    try:
        secret_key = client.secret
    except AttributeError:
        raise BuckarooException("No Buckaroo secret key in settings")

    urlencoded_signature = "".join(['{0}={1}'.format(k, v) for k, v in sorted(data.items())
                                    if k is not None and (k.startswith("BRQ_") or
                                    k.startswith("ADD_") or k.startswith("CUST_")) and
                                    not k.startswith("BRQ_SIGNATURE")]) + secret_key
    raw_signature = urllib.parse.unquote(urlencoded_signature)
    signature = hashlib.sha1(raw_signature.encode('utf-8')).hexdigest()
    if buckaroo_signature == signature:
        return True
    return False


def buckaroo_api_call(transaction, url, method, data=None):

    auth_header = AuthHeader(transaction=transaction,
                             url=url,
                             json=data,
                             method=method.upper()).get_auth_header()

    headers = {'Authorization': auth_header, 'Content-Type': 'application/json'}
    logger.info("API call for transaction: {0}, key {1}"
                .format(transaction.id, transaction.transaction_key))

    if method == 'POST':
        res = requests.post(url, headers=headers, json=data)
    if method == 'GET':
        res = requests.get(url, headers=headers)

    logger.info("API response: {0}".format(res.json()))

    return res


def add_creditcard_json(body, transaction, action):
    result = body.copy()

    card = transaction.card.lower()

    if not card or card not in ['visa', 'mastercard']:
            raise BuckarooException({"message": "Missing or erroneous field",
                                     "field": "card"})

    p1 = OrderedDict(Name='RecurringInterval',
                     Value='')

    p2 = OrderedDict(Name='CustomerCode',
                     Value='')

    creditcard = OrderedDict(name=card,
                             Parameters=[p1, p2])

    if action == 'pay':
        creditcard.update(Action='Pay')

    if action == 'refund':
        creditcard.update(Action='Refund')

    result['Services']['ServiceList'].append(creditcard)

    return result


def add_ideal_json(body, transaction, action):
    from .actions import BANK_CODES

    result = body.copy()
    bank_code = transaction.bank_code
    bank_codes = [x[0] for x in BANK_CODES]

    if not bank_code or bank_code not in bank_codes:
        raise BuckarooException({"message": "Missing or erroneous field",
                                 "field": "bank_code"})

    p1 = OrderedDict(Name='issuer',
                     Value=bank_code)

    ideal = OrderedDict(Name='ideal',
                        Version=2,
                        Parameters=[p1])

    if action == 'pay':
        ideal.update(Action='Pay')

    if action == 'refund':
        ideal.update(Action='Refund')

    result['Services']['ServiceList'].append(ideal)

    return result


def add_refund_json(body, transaction, amount):
    result = body.copy()
    result.update(AmountCredit=float(amount),
                  OriginalTransactionKey=transaction.transaction_key)
    return result


def add_pay_json(body, transaction, client):
    result = body.copy()

    return_url = "/get/from/client"

    if client and client.return_url:
        return_url = ''.join([client.return_url,
                              reverse('guts_payment_return',
                                      kwargs={'pk': transaction.order.id})])

    result.update(payment_method=transaction.payment_method,
                  bank_code=transaction.bank_code,
                  cardname=transaction.card,
                  AmountDebit=float(transaction.order.total),
                  ReturnURL=return_url)

    return result


def get_base_transaction_json(transaction, client):
    body = OrderedDict(Invoice=str(transaction.uuid),
                       Currency="EUR",
                       Services=OrderedDict(ServiceList=[]),
                       CustomParameters=OrderedDict(List=[OrderedDict(Name="client_id", Value=client.id)]))
    return body


def get_buckaroo_status_code(response={}):
    """Get the status from the Buckaroo transaction."""
    try:
        return response['Status']['Code']['Code']
    except KeyError:
        raise BuckarooException({"message": "Buckaroo status code not found"})


def get_payment_key(response={}):
    # Save payment identifier
    try:
        return response['PaymentKey']
    except KeyError:
        raise BuckarooException({'message': "PaymentKey not found"})


def get_transaction_key(response={}):
    # Save transaction key identifier
    try:
        return response['Key']
    except KeyError:
        raise BuckarooException({'message': "Transaction 'Key' not found"})


def get_key(response={}, key_name=None):
    try:
        return response[key_name]
    except KeyError:
        raise BuckarooException({'message': "{0} not found".format(key_name)})


def get_redirect_url(response={}):
    """Parse the response for the redirct url."""
    try:
        return response['RequiredAction']['RedirectURL']
    except KeyError:
        raise BuckarooException({"message": "No redirect url found"})


def verify_transaction_fields(transaction):
    if not transaction.payment_method:
        raise BuckarooException({"message": "Required field missing",
                                 "field": "payment_method"})

    if transaction.payment_method not in ['creditcard', 'ideal']:
        raise BuckarooException({"message": "Unknown payment method",
                                 "field": "payment_method"})

    if not transaction.order.id:
        raise BuckarooException({"message": "Required field missing",
                                 "field": "order.id"})

    if not transaction.order.total:
        raise BuckarooException({"message": "Required field missing",
                                 "field": "order.total"})


def construct_url(client=None):
    from .actions import (BUCKAROO_BASE_TEST_URL, BUCKAROO_BASE_PRODUCTION_URL,
                          BUCKAROO_CHECKOUT_URL)
    if client.test_mode:
        return ''.join([BUCKAROO_BASE_TEST_URL,
                        BUCKAROO_CHECKOUT_URL])
    else:
        return''.join([BUCKAROO_BASE_PRODUCTION_URL,
                       BUCKAROO_CHECKOUT_URL])


def split_url(url):
    try:
        new_url = url.split("//", 1)[-1]
    except IndexError:
        new_url = ""
    return new_url
