from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'course', 'amount', 'currency', 'status', 'stripe_payment_intent_id', 'created_at']


class CreatePaymentIntentSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()