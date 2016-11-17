from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status


from .factories import TransactionFactory, OrderFactory, UserFactory


class TransactionAPIStatusTestCase(APITestCase):
    """Test status code of various HTTP request methods."""

    def assert_forbidden(self, response):
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_request(self):
        response = self.client.get(reverse('buckaroo_transaction_list'), format='json')
        self.assert_forbidden(response)

    def test_put_request(self):
        response = self.client.put(reverse('buckaroo_transaction_list'), format='json')
        self.assert_forbidden(response)

    def test_delete_request(self):
        response = self.client.delete(reverse('buckaroo_transaction_list'), format='json')
        self.assert_forbidden(response)


class TransactionAPITestCase(APITestCase):
    """Tests for the Transaction API endpoint."""
    def setUp(self):
        self.user = UserFactory.create()
        self.client.force_login(self.user)
        self.order = OrderFactory.create(total=100, owner=self.user, state='pending')

        self.ideal_data = dict(bank_code='ABNANL2A',
                               card=None,
                               order=1,
                               payment_method='ideal',
                               redirect_url=None,
                               status=None,
                               uuid=None)

    def test_order_does_not_exist(self):
        order_id = 100
        self.ideal_data['order'] = order_id
        response = self.client.post(reverse('buckaroo_transaction_list'),
                                    self.ideal_data,
                                    format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (response.data['order'][0] ==
                'Invalid pk "{0}" - object does not exist.'.format(order_id))

    def test_invalid_ideal_data(self):
        self.ideal_data['order'] = self.order.id
        self.ideal_data['bank_code'] = 'blabla'

        response = self.client.post(reverse('buckaroo_transaction_list'),
                                    self.ideal_data,
                                    format='json')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "'message': 'Missing or erroneous field'" in response.json()['detail']
        assert "'field': 'bank_code'" in response.json()['detail']

    def test_user_not_owner(self):
        user = UserFactory.create()
        order = OrderFactory.create(total=100, owner=user)
        self.ideal_data['order'] = order.id

        response = self.client.post(reverse('buckaroo_transaction_list'),
                                    self.ideal_data,
                                    format='json')
        print(response.status_code)
        print(response.content)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User is not owner of the order'

    def test_order_status_not_pending(self):

        order = OrderFactory.create(total=100, owner=self.user, state='new')
        self.ideal_data['order'] = order.id

        response = self.client.post(reverse('buckaroo_transaction_list'),
                                    self.ideal_data,
                                    format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data[0] == 'Incorrect order status: new'


class TransactionPushAPITestCase(APITestCase):
    """Tests for the Transaction Push endpoint."""

    def setUp(self):
        self.user = UserFactory.create()
        self.client.force_login(self.user)
        self.transaction = TransactionFactory.create()

    def test_get_not_allowed(self):
        response = self.client.get(reverse('buckaroo_push'),
                                   HTTP_HOST="buckaroo.com",
                                   format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'Only POST requests allowed.'

    def test_invalid_domain(self):
        response = self.client.post(reverse('buckaroo_push'),
                                    data={"Transaction": 100},
                                    HTTP_HOST="hacker.org",
                                    format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'Only Buckaroo server may do a push update.'

    def test_missing_buckaroo_server_address(self):
        response = self.client.post(reverse('buckaroo_push'),
                                    {},
                                    format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'Only Buckaroo server may do a push update.'

    def test_transaction_not_found(self):
        response = self.client.post(reverse('buckaroo_push'),
                                    data={"Transaction": 100},
                                    HTTP_HOST="buckaroo.com",
                                    format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data == 'Transaction not found'

    def test_valid_buckaroo_address(self):
        response = self.client.post(reverse('buckaroo_push'),
                                    {},
                                    HTTP_HOST="buckaroo.com")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == 'ok'
