from datetime import datetime

from django.http import JsonResponse

from .models import (
    GiftCard,
    Product,
    ProductPrice
)


def bad_request(message, code):
    return JsonResponse({'message': message}, status=code)


def get_product_price(request):
    params = request.GET

    if 'productCode' not in params or 'date' not in params:
        return bad_request(
            message='Missing "productCode" or "date" query parameters',
            code=422
        )

    else:
        product_code = params.get('productCode')
        date_input = params.get('date')
        gift_card_code = params.get('giftCardCode', None)

        # make sure date is in target format
        price_date = None
        try:
            price_date = datetime.strptime(date_input, '%b %d %Y')
        except ValueError:
            return bad_request(
                message='Date must be formatted e.g. Jun 01 2004',
                code=400
            )

        # make sure product exists
        product = None
        try:
            product = Product.objects.get(code=product_code)
        except Product.DoesNotExist:
            return bad_request(
                message=f'Product with code {product_code} not found!',
                code=404
            )

        lowest_price = product.prices.filter(
                           date_start__lte=price_date,
                           date_end__gte=price_date
                       ).order_by('price').first()

        # ensure a price exists for the requested date
        if not lowest_price:
            return bad_request(message='Price not set for that time!', code=404)

        response_payload = {
            'product': product.name,
            'price': lowest_price.formatted_amount
        }

        return JsonResponse(response_payload, status=200)
