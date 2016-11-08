import django_fsm
import logging
import urllib.parse

from django.utils import timezone
from django.conf import settings
from django.http import HttpResponse

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Transaction
from .serializers import TransactionSerializer
from .actions import Pay
from .exceptions import BuckarooException, BuckarooAPIException
from .utils import verify_buckaroo_signature, update_transaction_post

from .permissions import PostOnly, BuckarooServer


logger = logging.getLogger(__name__)


class TransactionList(generics.ListCreateAPIView):
    """List view for Transaction."""

    permission_classes = (PostOnly,)
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def perform_create(self, serializer):
        instance = serializer.save(status='new')

        if instance.order.owner != self.request.user:
            raise PermissionDenied(detail="User is not owner of the order")

        if instance.order.state != 'pending':
            raise ValidationError(detail="Incorrect order status: {0}"
                                  .format(instance.order.state))

        try:
            logger.info("Starting Buckaroo Paymnent for transaction {0}".format(instance.id))
            Pay(transaction=instance, testing=settings.TESTING).pay()
        except BuckarooException as err:
            logger.exception("Service exception: {0}".format(err))
            raise BuckarooAPIException(detail=err)


class TransactionDetail(generics.ListCreateAPIView):
    """Detail view for Transaction."""

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


def update_transaction(transaction=None, data=None):

    if not transaction or not data:
        return None

    try:
        code = data['Status']['Code']['Code']
    except KeyError:
        logger.error("Status code not found. Data: {0}".format(data))
        if transaction:
            logger.error("Transaction id: {0}".format(transaction.id))
        code = None

    if code:
        status = transaction.map_status(status_code=code)
        logger.info("Updating transaction {0} status to {1}".format(transaction.id, status))
        try:
            if status == transaction.STATUS_SUCCESS:
                transaction.success()
            elif status == transaction.STATUS_CANCELLED:
                transaction.cancelled()
            elif status == transaction.STATUS_FAILED:
                transaction.failed()
            elif status == transaction.STATUS_REJECTED:
                transaction.rejected()
            else:
                logger.error("Status not found: {0}".format(transaction.status))
        except django_fsm.TransitionNotAllowed as e:
            logger.error("Failed to change transaction status: {0}".format(e))

    transaction.last_push = timezone.now()

    transaction.save()

    return transaction


class PushView(APIView):
    """ View to handle the push update call from Buckaroo."""
    permission_classes = (BuckarooServer, PostOnly)

    def post(self, request, *args, **kwargs):

        t_data = request.data.get('Transaction', None)

        logger.info("Received Buckaroo API push. Data: {0}".format(t_data))

        if t_data:
            try:
                transaction = Transaction.objects.get(payment_key=t_data['PaymentKey'])
            except (Transaction.DoesNotExist, TypeError):
                logger.warning("Transaction not found")
                return Response("Transaction not found")

            update_transaction(transaction=transaction, data=t_data)

        return Response("ok")


def PaymentReturnRedirectView(request, pk, *args, **kwargs):
    """
        Buckaroo does a POST request to our server with payment information. Ember cannot
        handle the POST request while keeping that data. Therefore we let Buckaroo do the
        POST to a Django view which then redirects and reformats the data so Ember can
        parse it.
    """
    logger = logging.getLogger('buckaroo.redirect')

    logger.info("Redirecting user after payment from Django return url to Ember")

    response = HttpResponse("", status=302)

    data = request.POST

    if verify_buckaroo_signature(data):
        transaction = update_transaction_post(data)
    else:
        logger.warning(
            "Received POST request with invalid signature. Data: {0}".format(data))
        return HttpResponse("Invalid signature", status=500)

    # Add flag to indicate whether there was success,
    # failure or cancelation. The frontend can/will take different actions
    # based on that flag
    flag = "failed"

    if transaction.status == Transaction.STATUS_SUCCESS:
        flag = "success"
    elif transaction.status == Transaction.STATUS_CANCELLED:
        flag = "cancelled"

    data = dict(data)  # we can't add keys to a QueryDict
    data['flag'] = flag

    # let the frontend also know for which event it was
    data['event'] = transaction.order.tickets.first().event_id

    response['Location'] = ("{0}/orders/"
                            "paymentReturn/{1}/{2}").format(settings.EMBER_URL,
                                                            pk,
                                                            urllib.parse.urlencode(data))
    return response
