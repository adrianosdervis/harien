from django.urls import path
from . import views as shopViews
from cart import views as cartViews

# app_name = 'shop'

urlpatterns = [
    path('', cartViews.CartView.as_view(), name='cart'),
    path('confirm-order/', cartViews.ConfirmOrderView.as_view(), name='confirm-order'),
    path('checkout/', cartViews.CheckoutView.as_view(), name='checkout'),
    path('payment/', cartViews.PaymentView.as_view(), name='payment'),
    path('thanks/', cartViews.BankThankYouView.as_view(), name='bank-thanks'),
    path('door/thanks/', cartViews.DoorThankYouView.as_view(), name='door-thanks'),
    path('stripe/thanks/', cartViews.StripeThankYouView.as_view(),
         name='stripe-thanks'),
    path('<slug>/', shopViews.ProductDetailView.as_view(), name='product'),
    path('increase-quantity/<pk>/',
         cartViews.IncreaseQuantityView.as_view(), name='increase-quantity'),
    path('decrease-quantity/<pk>/',
         cartViews.DecreaseQuantityView.as_view(), name='decrease-quantity'),
    path('remove-from-cart/<pk>/',
         cartViews.RemoveFromCartView.as_view(), name='remove-from-cart'),
    path('orders/<pk>/', cartViews.OrderDetailView.as_view(), name='order-detail'),
    path('payment/stripe/', cartViews.StripePaymentView.as_view(),
         name='payment-stripe'),
    path('payment/bank/', cartViews.BankPaymentView.as_view(),
         name='payment-bank'),
    path('payment/door/', cartViews.DoorPaymentView.as_view(),
         name='payment-door'),
    path('webhooks/stripe/', cartViews.stripe_webhook_view, name='stripe-webhook'),

]
