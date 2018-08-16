from datetime import datetime

from django.http import HttpResponseBadRequest, Http404, JsonResponse
from django.shortcuts import get_object_or_404

from .models import (
    GiftCard,
    Product,
    ProductPrice
)


def get_product_price(request):
    params = request.GET

    if 'productCode' not in params or 'date' not in params:
        return HttpResponseBadRequest('Missing "productCode" or "date" query parameters')

    else:
        product_code = params.get('productCode')
        date_input = params.get('date')
        gift_card_code = params.get('giftCardCode', None)

        # make sure date is in target format
        price_date = None
        try:
            price_date = datetime.strptime(date_input, '%b %d %Y').date()
        except ValueError:
            return HttpResponseBadRequest('Date must be formatted e.g. Jun 01 2004')

        product = get_object_or_404(Product, code=product_code)

        lowest_price = product.prices.filter(
                           date_start__lte=price_date,
                           date_end__gte=price_date
                       ).order_by('price').first()

        # ensure a price exists for the requested date
        if not lowest_price:
            raise Http404('Price not set for that time!')

        response_payload = {
            'product': product.name,
            'price': lowest_price.formatted_amount
        }

        if gift_card_code:
            gift_card = get_object_or_404(GiftCard, code=gift_card_code)
            valid = True
            if gift_card.date_end and gift_card.date_end < price_date:
                valid = False
            elif gift_card.date_start and gift_card.date_start > price_date:
                valid = False
            else:
                adjusted_price = lowest_price.price - gift_card.amount

                if adjusted_price < 0:
                    adjusted_price = 0

                response_payload['price'] = '${0:.2f}'.format(adjusted_price / 100)
                response_payload['message'] = 'Gift card applied at that date'

            if not valid:
                response_payload['message'] = 'Gift card not applicable at that date'

        return JsonResponse(response_payload, status=200)
