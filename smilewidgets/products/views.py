from django.http import JsonResponse
from pprint import pprint


def get_product_price(request):
    params = request.GET

    if 'productCode' not in params or 'date' not in params:
        message = 'Missing "productCode" or "date" query parameters'
        status_code = 422
    else:
        product_code = params.get('productCode')
        date = params.get('date')
        message = f'Product code is {product_code}; Date is {date}'
        status_code = 200

    return JsonResponse({'message': message}, status=status_code)
