from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class UserListView(APIView):
    def get(self, request):
        return Response({'message': 'User list endpoint'}, status=status.HTTP_200_OK)


class UserDetailView(APIView):
    def get(self, request, pk):
        return Response({'message': f'User detail endpoint for user {pk}'}, status=status.HTTP_200_OK)