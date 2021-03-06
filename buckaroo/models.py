import uuid
import logging

from django.db import models

from django_fsm import FSMField, transition

from order.models import Order
from utils.models import TimeStampedModel

from actstream import action

logger = logging.getLogger(__name__)

BUCKAROO_190_SUCCESS = 190
BUCKAROO_490_FAILED = 490
BUCKAROO_491_VALIDATION_FAILURE = 491
BUCKAROO_492_TECHNICAL_FAILURE = 492
BUCKAROO_690_REJECTED = 690
BUCKAROO_790_PENDING_INPUT = 790
BUCKAROO_791_PENDING_PROCESSING = 791
BUCKAROO_792_AWAITING_CONSUMER = 792
BUCKAROO_793_ON_HOLD = 793
BUCKAROO_890_CANCELLED_BY_USER = 890
BUCKAROO_891_CANCELLED_BY_MERCHANT = 891

BUCKAROO_STATUSES = (
    (BUCKAROO_190_SUCCESS, 'Success'),
    (BUCKAROO_490_FAILED, 'Failed'),
    (BUCKAROO_491_VALIDATION_FAILURE, 'Validation Failure'),
    (BUCKAROO_492_TECHNICAL_FAILURE, 'Technical Failure'),
    (BUCKAROO_690_REJECTED, 'Rejected'),
    (BUCKAROO_790_PENDING_INPUT, 'Pending input'),
    (BUCKAROO_791_PENDING_PROCESSING, 'Pending processing'),
    (BUCKAROO_792_AWAITING_CONSUMER, 'Awaiting consumer'),
    (BUCKAROO_793_ON_HOLD, 'On Hold'),
    (BUCKAROO_890_CANCELLED_BY_USER, 'Cancelled By User'),
    (BUCKAROO_891_CANCELLED_BY_MERCHANT, 'Cancelled By Merchant')
)


class Transaction(TimeStampedModel):
    """A transaction is a payment attempt for an Order."""

    PAYMENT_METHODS = (
        ('ideal', "iDeal"),
        ('creditcard', "Creditcard")
    )

    STATUS_NEW = "new"
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REJECTED = "rejected"

    payment_method = models.CharField(max_length=300, choices=PAYMENT_METHODS)
    payment_key = models.CharField(max_length=300, blank=True, null=True)
    transaction_key = models.CharField(max_length=300, blank=True, null=True)
    refunded = models.BooleanField(default=False)
    order = models.ForeignKey(Order)
    status = FSMField(default=STATUS_NEW, protected=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    redirect_url = models.CharField(max_length=500, blank=True, null=True)
    card = models.CharField(max_length=100, blank=True, null=True)
    bank_code = models.CharField(max_length=100, blank=True, null=True)
    last_push = models.DateTimeField(blank=True, null=True)

    def map_status(self, status_code=None):
        if not status_code:
            return None

        if status_code == BUCKAROO_190_SUCCESS:
            return self.STATUS_SUCCESS

        if status_code in (BUCKAROO_890_CANCELLED_BY_USER,
                           BUCKAROO_891_CANCELLED_BY_MERCHANT):
            return self.STATUS_CANCELLED

        if status_code in (BUCKAROO_790_PENDING_INPUT,
                           BUCKAROO_791_PENDING_PROCESSING,
                           BUCKAROO_792_AWAITING_CONSUMER,
                           BUCKAROO_793_ON_HOLD):
            return self.STATUS_PENDING

        if status_code == BUCKAROO_690_REJECTED:
            return self.STATUS_REJECTED

        if status_code in (BUCKAROO_490_FAILED,
                           BUCKAROO_491_VALIDATION_FAILURE,
                           BUCKAROO_492_TECHNICAL_FAILURE):
            return self.STATUS_FAILED

    @transition(field=status, source=STATUS_NEW, target=STATUS_PENDING)
    def pending(self):
        action.send(self, verb="transitioned to pending")

    @transition(field=status, source=STATUS_PENDING, target=STATUS_SUCCESS)
    def success(self):
        logger.info("Updating order {0} to 'completed'".format(self.order.id))
        self.order.completed()
        self.order.save()
        action.send(self, verb="completed", target_object=self.order)

    @transition(field=status, source=[STATUS_NEW,
                                      STATUS_PENDING], target=STATUS_FAILED)
    def failed(self):
        logger.info("Updating order {0} to 'failed'".format(self.order.id))
        self.order.failure()
        self.order.save()
        action.send(self, verb="failed", target_object=self.order)

    @transition(field=status, source=STATUS_PENDING, target=STATUS_CANCELLED)
    def cancelled(self):
        self.order.cancel_pay()
        self.order.save()
        action.send(self, verb="cancelled", target_object=self.order)

    @transition(field=status, source=STATUS_PENDING, target=STATUS_REJECTED)
    def rejected(self):
        logger.info("Updating order {0} to 'failed'".format(self.order.id))
        self.order.failure()
        self.order.save()
        action.send(self, verb="rejected", target_object=self.order)

    def __str__(self):
        return "Transaction {0} with status {1}".format(self.id, self.status)
