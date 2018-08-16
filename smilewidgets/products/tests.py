import json

from django.test import Client, TestCase
from django.test.utils import setup_test_environment
from django.utils.http import urlencode

from products.models import (
    GiftCard,
    Product,
    ProductPrice
)


class ProductsViewTests(TestCase):
    def setUp(self):
        product_1 = Product(name='Big Widget', code='big_widget')
        product_1.save()

        product_2 = Product(name='Small Widget', code='sm_widget')
        product_2.save()

        gift_card_1 = GiftCard(
            code='10OFF',
            amount=1000,
            date_start='2018-07-01',
            date_end=None
        )
        gift_card_1.save()

        gift_card_2 = GiftCard(
            code='50OFF',
            amount=5000,
            date_start='2018-07-01',
            date_end=None
        ).save()

        gift_card_3 = GiftCard(
            code='250OFF',
            amount=25000,
            date_start='2018-12-01',
            date_end='2019-01-01'
        ).save()

        price_1 = ProductPrice(
            price=100000,
            description='Big Widget Price in 2018',
            date_start='2018-01-01',
            date_end='2018-12-31',
            product=product_1
        )
        price_1.save()

        price_2 = ProductPrice(
            price=9900,
            description='Small Widget Price in 2018',
            date_start='2018-01-01',
            date_end='2018-12-31',
            product=product_2
        )
        price_2.save()

        price_3 = ProductPrice(
            price=80000,
            description='Big Widget Black Friday Price in 2018',
            date_start='2018-11-23',
            date_end='2018-11-25',
            product=product_1
        )
        price_3.save()

        price_4 = ProductPrice(
            price=0,
            description='Small Widget Black Friday Price in 2018',
            date_start='2018-11-23',
            date_end='2018-11-25',
            product=product_2
        )
        price_4.save()

        price_5 = ProductPrice(
            price=120000,
            description='Big Widget Price in 2019',
            date_start='2019-01-01',
            date_end='2019-12-31',
            product=product_1
        )
        price_5.save()

        price_6 = ProductPrice(
            price=12500,
            description='Small Widget Price in 2019',
            date_start='2019-01-01',
            date_end='2019-12-31',
            product=product_2
        )
        price_6.save()


    def test_bad_params(self):
        """
        If 'date' or 'productCode' are missing, client should be notified
        """
        response = self.client.get('/api/get-price')
        self.assertEqual(response.status_code, 400)


    def test_good_params(self):
        params = {'date': 'nov 11 2018', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)


    def test_bad_date_format(self):
        """
        Giving malformed 'date' param throws error
        """
        params = {'date': 'wat 11 2018', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Date must be formatted e.g. Jun 01 2004')

    def test_bad_product_code(self):
        params = {'date': 'nov 11 2018', 'productCode': 'definitelyshouldnotwork'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 404)

    def test_date_out_of_range(self):
        """
        Requesting a price for a product for a date which hasn't been set should throw
        """
        params = {'date': 'nov 11 2017', 'productCode': 'sm_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 404)

        params = {'date': 'nov 11 2020', 'productCode': 'sm_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 404)

        params = {'date': 'nov 11 2017', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 404)

        params = {'date': 'nov 11 2020', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 404)


    def test_getting_price(self):
        params = {'date': 'nov 11 2018', 'productCode': 'sm_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Small Widget')
        self.assertEqual(body['price'], '$99.00')

        params = {'date': 'nov 11 2019', 'productCode': 'sm_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Small Widget')
        self.assertEqual(body['price'], '$125.00')

        params = {'date': 'nov 11 2018', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Big Widget')
        self.assertEqual(body['price'], '$1000.00')

        params = {'date': 'nov 11 2019', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Big Widget')
        self.assertEqual(body['price'], '$1200.00')


    def test_getting_price_during_sale(self):
        params = {'date': 'nov 23 2018', 'productCode': 'sm_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Small Widget')
        self.assertEqual(body['price'], '$0.00')

        params = {'date': 'nov 25 2018', 'productCode': 'big_widget'}
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Big Widget')
        self.assertEqual(body['price'], '$800.00')


    def test_applying_gift_cards(self):
        params = {
            'date': 'jul 01 2018',
            'productCode': 'big_widget',
            'giftCardCode': '10OFF'
        }
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Big Widget')
        self.assertEqual(body['price'], '$990.00')
        self.assertEqual(body['message'], 'Gift card applied at that date')

        # this one shouldn't apply at this time
        params['date'] = 'jun 25 2018'
        response = self.client.get('/api/get-price', params)
        body = json.loads(response.content)
        self.assertEqual(body['price'], '$1000.00')
        self.assertEqual(body['message'], 'Gift card not applicable at that date')

        # this one should apply at this time
        params['date'] = 'dec 12 2018'
        params['giftCardCode'] = '250OFF'
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['product'], 'Big Widget')
        self.assertEqual(body['price'], '$750.00')
        self.assertEqual(body['message'], 'Gift card applied at that date')

        # but not here
        params['date'] = 'jun 25 2019'
        params['giftCardCode'] = '250OFF'
        response = self.client.get('/api/get-price', params)
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.content)
        self.assertEqual(body['price'], '$1200.00')
        self.assertEqual(body['message'], 'Gift card not applicable at that date')
