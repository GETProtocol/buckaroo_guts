import pytest


@pytest.mark.django_db(transaction=False)
class TestStates:

    def test_initialstate(self, transaction):
        print("HELP!")
        assert transaction.status == transaction.STATUS_NEW

    def test_in_pending_state(self, transaction):
        transaction.pending()
        assert transaction.status == transaction.STATUS_PENDING

    def test_success_state(self, transaction):
        transaction.pending()
        transaction.success()
        assert transaction.status == transaction.STATUS_SUCCESS

    def test_failed_state(self, transaction):
        transaction.pending()
        transaction.failed()
        assert transaction.status == transaction.STATUS_FAILED

    def test_cancelled_state(self, transaction):
        transaction.pending()
        transaction.cancelled()
        assert transaction.status == transaction.STATUS_CANCELLED

    def test_rejected_state(self, transaction):
        transaction.pending()
        transaction.rejected()
        assert transaction.status == transaction.STATUS_REJECTED


@pytest.mark.django_db(transaction=False)
class TestOrderStateUpdate:

    def test_pending(self, transaction):
        assert (transaction.order.state ==
                transaction.order.STATUS_PENDING)

        assert transaction.status == transaction.STATUS_NEW

        transaction.pending()

        assert (transaction.order.state ==
                transaction.order.STATUS_PENDING)

    def test_transaction_pending_fixture_status(self, transaction_pending):
        assert transaction_pending.order.state == transaction_pending.order.STATUS_PENDING
        assert transaction_pending.status == transaction_pending.STATUS_PENDING

    def test_success(self, transaction_pending):

        transaction_pending.success()

        assert transaction_pending.status == transaction_pending.STATUS_SUCCESS
        assert transaction_pending.order.state == transaction_pending.order.STATUS_COMPLETED

    def test_failed(self, transaction_pending):

        transaction_pending.failed()

        assert transaction_pending.status == transaction_pending.STATUS_FAILED
        assert transaction_pending.order.state == transaction_pending.order.STATUS_FAILED

    def test_cancelled(self, transaction_pending):

        transaction_pending.cancelled()

        assert transaction_pending.status == transaction_pending.STATUS_CANCELLED
        assert transaction_pending.order.state == transaction_pending.order.STATUS_CANCELLED

    def test_rejected(self, transaction_pending):

        transaction_pending.rejected()

        assert transaction_pending.status == transaction_pending.STATUS_REJECTED
        assert transaction_pending.order.state == transaction_pending.order.STATUS_FAILED
