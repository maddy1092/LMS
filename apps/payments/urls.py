from django.urls import path
from . import views

urlpatterns = [
    path('create-payment-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
]