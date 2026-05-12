import stripe
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import HttpResponse

from apps.courses.models import Course
from apps.courses.views import is_student
from .serializers import CreatePaymentIntentSerializer
from .models import Payment
from drf_spectacular.utils import extend_schema

stripe.api_key = settings.STRIPE_SECRET_KEY


@extend_schema(
    summary="Create a Stripe PaymentIntent for a paid course",
    request=CreatePaymentIntentSerializer,
    responses={201: {"description": "Returns client_secret and payment_intent_id"}},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """Create a Stripe PaymentIntent for a course."""
    serializer = CreatePaymentIntentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    course_id = serializer.validated_data['course_id']
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    if not is_student(request.user):
        return Response({'error': 'Only students can purchase courses'}, status=status.HTTP_403_FORBIDDEN)
    
    if course.course_enrollments.filter(student=request.user, is_active=True).exists():
        return Response({'error': 'Already enrolled in this course'}, status=status.HTTP_400_BAD_REQUEST)
    
    if course.is_free:
        return Response({'error': 'This course is free. Use enroll endpoint directly.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(course.price * 100),
            currency=course.currency.lower(),
            metadata={
                'course_id': course.id,
                'user_id': request.user.id,
                'user_email': request.user.email,
            },
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never',  # Disable redirect-based payment methods
            },
        )
        
        Payment.objects.create(
            user=request.user,
            course=course,
            stripe_payment_intent_id=intent.id,
            amount=course.price,
            currency=course.currency,
            status='pending'
        )
        
        return Response({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id,
        }, status=status.HTTP_201_CREATED)
        
    except stripe.error.StripeError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(exclude=True)
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    
    if not endpoint_secret:
        return HttpResponse(status=400, content="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent['id'])
            payment.status = 'succeeded'
            payment.save()
            
            # Create enrollment if not exists
            from apps.courses.models import CourseEnrollment
            enrollment, created = CourseEnrollment.objects.get_or_create(
                student=payment.user,
                course=payment.course,
                defaults={
                    'status': 'enrolled',
                    'is_active': True,
                }
            )
            if not created and not enrollment.is_active:
                enrollment.is_active = True
                enrollment.status = 'enrolled'
                enrollment.save()
        except Payment.DoesNotExist:
            pass
    
    return HttpResponse(status=200)