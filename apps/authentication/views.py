from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from apps.users.models import User, UserProfile
from .serializers import UserRegistrationSerializer, UserLoginSerializer, ChangePasswordSerializer, UserProfileSerializer
from .serializers_extra import ForgotPasswordSerializer, ResetPasswordSerializer, EmailVerificationSerializer
from .models import EmailVerificationToken, PasswordResetToken
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


@extend_schema(
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            description='User registered successfully',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'user_id': 1,
                        'email': 'user@example.com',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Validation errors')
    },
    summary='Register new user',
    description='Create a new user account with email and profile information'
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user_id': user.id,
            'email': user.email,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserLoginSerializer,
    responses={
        200: OpenApiResponse(
            description='Login successful',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'user_id': 1,
                        'email': 'user@example.com',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'profile': {
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'role_name': 'Student'
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Invalid credentials')
    },
    summary='User login',
    description='Authenticate user and return JWT tokens'
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        # Get user profile
        try:
            profile = UserProfile.objects.get(user=user)
            profile_data = UserProfileSerializer(profile).data
        except UserProfile.DoesNotExist:
            profile_data = {}
            
        return Response({
            'user_id': user.id,
            'email': user.email,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'profile': profile_data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request={
        'type': 'object',
        'properties': {
            'refresh': {'type': 'string', 'description': 'Refresh token to blacklist'}
        }
    },
    responses={
        200: OpenApiResponse(
            description='Logout successful',
            examples=[
                OpenApiExample(
                    'Success',
                    value={'message': 'Successfully logged out'}
                )
            ]
        )
    },
    summary='User logout',
    description='Blacklist refresh token and logout user'
)
@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        return Response({
            'access': str(token.access_token),
            'refresh': str(token)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(
            description='Password changed successfully',
            examples=[
                OpenApiExample(
                    'Success',
                    value={
                        'message': 'Password changed successfully',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='Validation errors')
    },
    summary='Change password',
    description='Change user password (requires authentication)'
)
@api_view(['POST'])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Generate new tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Password changed successfully',
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Create password reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Send email
        reset_url = f"http://localhost:3000/reset-password?token={reset_token.token}"
        send_mail(
            'Password Reset Request',
            f'Click here to reset your password: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        reset_token = PasswordResetToken.objects.get(token=token, used=False)
        user = reset_token.user
        
        # Update password
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        verification_token = EmailVerificationToken.objects.get(token=token)
        user = verification_token.user
        
        # Mark user as verified (add email_verified field to User model if needed)
        # For now, we'll delete the token to mark as verified
        verification_token.delete()
        
        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_verification(request):
    user = request.user
    
    # Delete existing token if any
    EmailVerificationToken.objects.filter(user=user).delete()
    
    # Create new token
    verification_token = EmailVerificationToken.objects.create(user=user)
    
    # Send email
    verify_url = f"http://localhost:3000/verify-email?token={verification_token.token}"
    send_mail(
        'Email Verification',
        f'Click here to verify your email: {verify_url}',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    return Response({'message': 'Verification email sent'}, status=status.HTTP_200_OK)