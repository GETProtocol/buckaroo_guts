import pytest
import re

from buckaroo.exceptions import BuckarooException
from buckaroo.utils import (split_url, verify_buckaroo_signature,
                            get_redirect_url, get_transaction_key, get_payment_key,
                            get_buckaroo_status_code, verify_transaction_fields)

from buckaroo.auth import generate_nonce, generate_timestamp


class TestUtils:
    def test_split_url_success(self):
        result = split_url('http://properurl.com')
        assert result == 'properurl.com'

    def test_split_url_error(self):
        result = split_url('www.properurl.com')
        assert result == 'www.properurl.com'

    def test_construct_url(self):
        pass

    def test_construct_url_no_settings(self):
        pass

    def test_get_redirect_url(self):
        url = "www.test.com"
        res = dict(RequiredAction=dict(RedirectURL=url))
        result = get_redirect_url(res)
        assert result == url

    def test_get_redirect_exception(self):
        res = dict()
        with pytest.raises(BuckarooException) as err:
            get_redirect_url(res)
        assert err.value.args[0]['message'] == "No redirect url found"

    def test_get_transaction_key_success(self):
        result = get_transaction_key(dict(Key="test"))
        assert result == 'test'

    def test_get_transaction_key_exception(self):
        with pytest.raises(BuckarooException) as err:
            get_transaction_key({})
        assert err.value.args[0]['message'] == "Transaction 'Key' not found"

    def test_get_payment_key_success(self):
        result = get_payment_key(dict(PaymentKey="test"))
        assert result == 'test'

    def test_get_payment_key_exception(self):
        with pytest.raises(BuckarooException) as err:
            get_payment_key({})
        assert err.value.args[0]['message'] == "PaymentKey not found"

    def test_get_buckaroo_status_code(self):
        res = dict(Status=dict(Code=dict(Code="test")))
        assert get_buckaroo_status_code(res) == 'test'

    def test_get_buckaroo_status_code_exception(self):
        with pytest.raises(BuckarooException) as err:
            get_buckaroo_status_code({})
        assert err.value.args[0]['message'] == "Buckaroo status code not found"

    @pytest.mark.django_db(transaction=False)
    def test_missing_required_field_payment_method(self, transaction):

        transaction.payment_method = None

        with pytest.raises(BuckarooException) as err:
            verify_transaction_fields(transaction=transaction)
        assert err.value.args[0]['message'] == "Required field missing"
        assert err.value.args[0]['field'] == "payment_method"

    @pytest.mark.django_db(transaction=False)
    def test_missing_required_field_order_id(self, transaction):

        transaction.payment_method = 'ideal'
        transaction.order.id = None

        with pytest.raises(BuckarooException) as err:
            verify_transaction_fields(transaction=transaction)
        assert err.value.args[0]['message'] == "Required field missing"
        assert err.value.args[0]['field'] == "order.id"

    @pytest.mark.django_db(transaction=False)
    def test_missing_required_field_order_total(self, transaction):

        transaction.payment_method = 'ideal'
        transaction.order.total = None

        with pytest.raises(BuckarooException) as err:
            verify_transaction_fields(transaction=transaction)
        assert err.value.args[0]['message'] == "Required field missing"
        assert err.value.args[0]['field'] == "order.total"

    @pytest.mark.django_db(transaction=False)
    def test_unknown_payment_method(self, transaction):

        transaction.payment_method = 'direct_debit'

        with pytest.raises(BuckarooException) as err:
            verify_transaction_fields(transaction=transaction)
        assert err.value.args[0]['message'] == "Unknown payment method"
        assert err.value.args[0]['field'] == "payment_method"


class TestNonce:
    def test_length(self):
        result = generate_nonce()
        assert len(result) == 8

        result = generate_nonce(length=10)
        assert len(result) == 10

    def test_integers_only(self):
        result = generate_nonce()

        pattern = '^\d+$'
        assert re.match(pattern, result) is not None

        pattern = '^[A-Z][a-z]+$'
        assert re.match(pattern, result) is None


class TestTimestamp:
    def test_type(self):
        assert type(generate_timestamp()) is int


@pytest.fixture
def full_data():
    return {'BRQ_STATUSCODE': '190',
            'BRQ_PAYMENT_METHOD': 'ideal',
            'BRQ_TIMESTAMP': '2016-09-06 16:06:54',
            'BRQ_STATUSCODE_DETAIL': 'S001',
            'BRQ_SERVICE_IDEAL_CONSUMERBIC': 'RABONL2U',
            'BRQ_TEST': 'true',
            'BRQ_CUSTOMER_NAME': 'J. de Tèster',
            'BRQ_PAYMENT': '4ED2032582DF418BADF21587BE406453',
            'BRQ_SERVICE_IDEAL_CONSUMERNAME': 'J. de Tèster',
            'BRQ_WEBSITEKEY': '3LtvvAcZub',
            'BRQ_AMOUNT': '150.00',
            'BRQ_PAYER_HASH': '4ea533707efb6aab53686ab557d6c74c192fa80596f2582d6c'
                              '862885d305283db9a4055b00e10838de57296124f85bbfd36d'
                              '34f2c00b9d480497d5016b54bcd4',
            'BRQ_TRANSACTIONS': '0475B403C11A4AB4A5F69ACBCAA2C3D1',
            'BRQ_CURRENCY': 'EUR',
            'BRQ_STATUSMESSAGE': 'Transaction successfully processed',
            'BRQ_INVOICENUMBER': '4e6703b4-193b-41dc-b2b5-7c4c6336c741',
            # Changed signature for test value of secret key
            'BRQ_SIGNATURE': 'f5d28e00651fa5862691292563b5e719aedebc71',
            #'BRQ_SIGNATURE': '78dd56cb548c807eada3e232d5ad5c45e5157c96',
            'BRQ_SERVICE_IDEAL_CONSUMERISSUER': 'ABNAMRO Bank ',
            'BRQ_SERVICE_IDEAL_CONSUMERIBAN': 'NL44RABO0123456789'}


@pytest.mark.django_db(transaction=False)
class TestSignatureUtils:

    def test_valid_signature(self, full_data, gutsclient):
        assert verify_buckaroo_signature(full_data, gutsclient)
    # def test_invalid_no_settings_key(self, full_data, gutsclient):
    #     with pytest.raises(BuckarooException) as err:
    #         verify_buckaroo_signature(full_data, gutsclient)
    #     assert err.value.args[0] == "No Buckaroo secret key in settings"

    @pytest.mark.parametrize('field', sorted(full_data().keys()))
    def test_invalid_signature_removed_field(self, full_data, field, gutsclient):
        del full_data[field]
        assert not verify_buckaroo_signature(full_data, gutsclient)

    def test_valid_signature_added_filtered_and_empty_fields(self,
                                                             full_data, gutsclient):
        full_data['BLA_Bla'] = '12345'
        full_data['BLA_Bla2'] = None
        assert verify_buckaroo_signature(full_data, gutsclient)
