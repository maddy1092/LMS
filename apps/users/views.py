from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from apps.users.models import User, UserProfile


class UserListView(APIView):
    def get(self, request):
        return Response({'message': 'User list endpoint'}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    def get(self, request, pk):
        return Response({'message': f'User detail endpoint for user {pk}'}, status=status.HTTP_200_OK)

class UsersByRoleView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary='Get users by role',
        description='Get users filtered by role (Teacher or Student)',
        parameters=[
            OpenApiParameter('role', OpenApiTypes.STR, required=True, description='Role: Teacher or Student')
        ],
        responses={200: {
            'type': 'object',
            'properties': {
                'users': {'type': 'array', 'items': {'type': 'object'}},
                'count': {'type': 'integer'},
                'role': {'type': 'string'}
            }
        }}
    )
    
    def get(self, request):
        role_name = request.GET.get('role', '').capitalize()
        User = get_user_model()

        
        if not role_name or role_name not in ['Teacher', 'Student']:
            return Response(
                {'error': 'Provide valid role: Teacher, or Student'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get users with specific role
        users = User.objects.filter(
            userprofile__role__name=role_name
        ).select_related('userprofile')
        
        data = []
        for user in users:
            profile = user.userprofile
            data.append({
                'id': user.id,
                'email': user.email,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'role': role_name,
                'date_joined': user.date_joined,
                'is_active': user.is_active
            })
        
        return Response({'users': data, 'count': len(data), 'role': role_name})

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary='Get user profile',
        description='Get current user profile',
        responses={200: {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'email': {'type': 'string'},
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'avatar': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'country': {'type': 'string'},
                'language_preference': {'type': 'string'},
                'timezone': {'type': 'string'},
                'role': {'type': 'string'},
                'date_joined': {'type': 'string'},
                'is_active': {'type': 'boolean'}
            }
        }}
    )
    
    def get(self, request):
        """Get current user profile - GET request"""
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
            data = {
                'id': user.id,
                'email': user.email,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'avatar': profile.avatar,
                'phone_number': profile.phone_number,
                'country': profile.country,
                'language_preference': profile.language_preference,
                'timezone': profile.timezone,
                'role': profile.role.name if profile.role else None,
                'date_joined': user.date_joined,
                'is_active': user.is_active
            }
            return Response(data)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class UserProfileUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary='Update user profile',
        description='Update current user profile',
        request={
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string'},
                'last_name': {'type': 'string'},
                'avatar': {'type': 'string'},
                'phone_number': {'type': 'string'},
                'country': {'type': 'string'},
                'language_preference': {'type': 'string'},
                'timezone': {'type': 'string'}
            }
        },
        responses={200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'updated_fields': {'type': 'array', 'items': {'type': 'string'}},
                'profile': {'type': 'object'}
            }
        }}
    )
    
    def post(self, request):
        """Update current user profile - POST request"""
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
            
            # Update user profile fields
            allowed_fields = ['first_name', 'last_name', 'avatar', 'phone_number', 
                             'country', 'language_preference', 'timezone']
            
            updated_fields = []
            for field in allowed_fields:
                if field in request.data:
                    setattr(profile, field, request.data[field])
                    updated_fields.append(field)
            
            if updated_fields:
                profile.save()
            
            return Response({
                'message': 'Profile updated successfully',
                'updated_fields': updated_fields,
                'profile': {
                    'first_name': profile.first_name,
                    'last_name': profile.last_name,
                    'avatar': profile.avatar,
                    'phone_number': profile.phone_number,
                    'country': profile.country,
                    'language_preference': profile.language_preference,
                    'timezone': profile.timezone,
                    'role': profile.role.name if profile.role else None
                }
            })
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )