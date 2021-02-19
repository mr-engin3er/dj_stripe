from django.urls import path
from .views import (
    SuccessView,
    CancelView,
    ProductLandingPageView,
    CreateCheckoutSessionView,
    StripeIntentView,
    stripe_webhook,
)

app_name = 'payment'

urlpatterns = [
    path('',ProductLandingPageView.as_view(),name=''),
    path('create-checkout-session/<pk>/',CreateCheckoutSessionView.as_view(),name='create-checkout-session'),
    path('success/',SuccessView.as_view(),name='success'),
    path('cancel/',CancelView.as_view(),name='cancel'),
    path('webhook/stripe',stripe_webhook,name='stripe-webhook'),
    path('create-payment-intent/<pk>/',StripeIntentView.as_view(),name='create-payment-intent'),

]
