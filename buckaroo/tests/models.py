from django.db import models

from django.contrib.auth.models import User
from django_fsm import FSMField, transition

from ..models import BasicOrderModel


class Ticket(models.Model):
    name = models.CharField(max_length=300, blank=True, null=True)


class Order(BasicOrderModel):

    STATUS_CREATED = "created"
    STATUS_PENDING = "pending"
    STATUS_FAILED = "failure"
    STATUS_CANCELLED = "cancelled"
    STATUS_TIMEOUT = "timeout"
    STATUS_COMPLETED = "completed"

    state = FSMField(default=STATUS_CREATED, protected=True)
    owner = models.ForeignKey(User, related_name="orders", null=True)
    tickets = models.ManyToManyField(Ticket, related_name="tickets")

    @transition(field=state, source=STATUS_CREATED, target=STATUS_PENDING)
    def start_pay(self):
        pass

    @transition(field=state, source=STATUS_PENDING, target=STATUS_COMPLETED)
    def completed(self):
        pass

    @transition(field=state, source=STATUS_PENDING, target=STATUS_CANCELLED)
    def cancel_pay(self):
        pass

    @transition(field=state, source=STATUS_PENDING, target=STATUS_FAILED)
    def failure(self):
        pass

    @transition(field=state, source=STATUS_PENDING, target=STATUS_TIMEOUT)
    def timeout(self):
        pass

    def __str__(self):
        return 'Order {} state {} for user {}'.format(self.id,
                                                      self.state,
                                                      self.owner)
