from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from django.contrib.auth import get_user_model

class UserListView(APIView):
    def get(self, request):
        return Response({'message': 'User list endpoint'}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    def get(self, request, pk):
        return Response({'message': f'User detail endpoint for user {pk}'}, status=status.HTTP_200_OK)

class UsersByRoleView(APIView):
    permission_classes = [permissions.AllowAny]
    
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