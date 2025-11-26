from rest_framework import serializers
from apps.users.models import User
from .models import EmailVerificationToken, PasswordResetToken


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_token(self, value):
        try:
            reset_token = PasswordResetToken.objects.get(token=value, used=False)
            if reset_token.is_expired():
                raise serializers.ValidationError('Token has expired')
            return value
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError('Invalid token')


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    
    def validate_token(self, value):
        try:
            verification_token = EmailVerificationToken.objects.get(token=value)
            if verification_token.is_expired():
                raise serializers.ValidationError('Token has expired')
            return value
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError('Invalid token')