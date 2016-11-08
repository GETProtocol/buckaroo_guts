from django.conf.urls import url, patterns
from . import views

urlpatterns = patterns(
    '',
    url(r'^transaction/$', views.TransactionList.as_view(),
        name='buckaroo_transaction_list'),
    url(r'^push', views.PushView.as_view(),
        name="buckaroo_push")
)
