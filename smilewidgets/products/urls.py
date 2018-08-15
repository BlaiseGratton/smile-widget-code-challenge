from django.urls import path

from . import views


urlpatterns = [
    path('get-price', views.get_product_price, name='get-product-price')
]
