from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User, UserProfile, Role
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailVerificationToken, PasswordResetToken


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role_name = serializers.CharField(write_only=True, required=False, default='Student')
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    avatar = serializers.URLField(required=False)
    phone_number = serializers.CharField(max_length=20, required=False)
    country = serializers.CharField(max_length=100, required=False)
    language_preference = serializers.CharField(max_length=10, required=False, default='en')
    timezone = serializers.CharField(max_length=50, required=False, default='UTC')

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'role_name', 'first_name', 'last_name', 'avatar', 'phone_number', 'country', 'language_preference', 'timezone']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_name = validated_data.pop('role_name', 'Student')
        
        # Extract profile fields
        profile_fields = {
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
            'avatar': validated_data.pop('avatar', ''),
            'phone_number': validated_data.pop('phone_number', ''),
            'country': validated_data.pop('country', ''),
            'language_preference': validated_data.pop('language_preference', 'en'),
            'timezone': validated_data.pop('timezone', 'UTC'),
        }
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Get role and create profile
        role = None
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            pass
            
        UserProfile.objects.create(user=user, role=role, **profile_fields)
        
        # Create email verification token
        EmailVerificationToken.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'avatar', 'phone_number', 'country', 'language_preference', 'timezone', 'role_name']