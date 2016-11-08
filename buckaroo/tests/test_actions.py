import pytest
from rest_framework import status

from ..models import BUCKAROO_790_PENDING_INPUT, BUCKAROO_190_SUCCESS
from ..actions import Pay, Refund
from ..exceptions import BuckarooException

from .test_unit import Response


@pytest.mark.django_db(transaction=False)
class TestPay:
    def test_invalid_status_code_api_request(self, transaction):
        codes = [status.HTTP_201_CREATED,
                 status.HTTP_404_NOT_FOUND,
                 status.HTTP_303_SEE_OTHER,
                 status.HTTP_500_INTERNAL_SERVER_ERROR]

        for code in codes:
            res = Response(status_code=code)
            with pytest.raises(BuckarooException) as err:
                Pay(transaction=transaction,
                    testing=True)._handle_transaction_response(response=res)
            assert err.value.args[0]['status'] == code

    def test_valid_api_statuscode_invalid_buckaroo_statuscode(self, transaction):

        res = Response(status_code=status.HTTP_200_OK,
                       Status={'Code': {'Code': status.HTTP_500_INTERNAL_SERVER_ERROR}})

        with pytest.raises(BuckarooException) as err:
            Pay(transaction=transaction,
                testing=True)._handle_transaction_response(response=res)
        err.value.args[0]["Buckaroo Status"] == status.HTTP_500_INTERNAL_SERVER_ERROR
        err.value.args[0]['message'] == "Invalid Buckaroo transaction status"

    def test_valid_api_statuscode_valid_buckaroo_statuscode(self, transaction):

        r_url = "www.test.com"

        assert transaction.status == 'new'
        assert transaction.redirect_url is None

        res = Response(status_code=status.HTTP_200_OK,
                       RequiredAction={'RedirectURL': r_url},
                       Status={'Code': {'Code': BUCKAROO_790_PENDING_INPUT}})

        Pay(transaction=transaction,
            testing=True)._handle_transaction_response(response=res)

        assert transaction.status == 'pending'
        assert transaction.redirect_url == r_url


@pytest.mark.django_db(transaction=False)
class TestRefund:
    def test_update_refund_info_missing_keys_isRefundable(self, transaction):

        res = {}
        with pytest.raises(BuckarooException) as err:
            Refund(transaction=transaction)._update_refund_info(res)

        assert err.value.args[0]['message'] == "'IsRefundable' key not in API response"

    def test_update_refund_info_update_object(self, transaction):

        refund = Refund(transaction=transaction)

        assert not refund.is_refundable
        assert refund.max_refund_amount == -1
        assert not refund.partial_allowed
        assert refund.refunded_amount == 0

        res = dict(IsRefundable=True,
                   MaximumRefundAmount=100,
                   AllowPartialRefund=True,
                   RefundedAmount=50)

        refund._update_refund_info(res)

        assert refund.is_refundable
        assert refund.max_refund_amount == 100
        assert refund.partial_allowed
        assert refund.refunded_amount == 50

    def test_handle_response_unsuccessful_api_call(self, transaction):
        codes = [status.HTTP_201_CREATED,
                 status.HTTP_404_NOT_FOUND,
                 status.HTTP_303_SEE_OTHER,
                 status.HTTP_500_INTERNAL_SERVER_ERROR]

        for code in codes:
            res = Response(status_code=code)
            with pytest.raises(BuckarooException) as err:
                Refund(transaction=transaction,
                       testing=True)._handle_transaction_response(response=res)
            assert err.value.args[0]['status'] == code

    def test_handle_response_invalid_buckaroo_status(self, transaction):
        res = Response(status_code=status.HTTP_200_OK,
                       Status={'Code': {'Code': status.HTTP_500_INTERNAL_SERVER_ERROR}})

        assert transaction.refunded is False

        with pytest.raises(BuckarooException) as err:
            Refund(transaction=transaction,
                   testing=True)._handle_transaction_response(response=res)

        err.value.args[0]["Buckaroo Status"] == status.HTTP_500_INTERNAL_SERVER_ERROR
        err.value.args[0]['message'] == "Invalid Buckaroo transaction status"

        assert transaction.refunded is False

    def test_successful_refund(self, transaction):
        res = Response(status_code=status.HTTP_200_OK,
                       Status={'Code': {'Code': BUCKAROO_190_SUCCESS}})

        assert transaction.refunded is False

        Refund(transaction=transaction,
               testing=True)._handle_transaction_response(response=res)

        assert transaction.refunded is True

    def test_handle_transaction_response_send_raw_res(self, transaction):
        res = Response(status_code=status.HTTP_200_OK,
                       Status={'Code': {'Code': BUCKAROO_190_SUCCESS}})

        assert transaction.refunded is False

        Refund(transaction=transaction,
               testing=True)._handle_transaction_response(response=res)

        assert transaction.refunded is True
