from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserListView.as_view(), name='user-list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('by-role/', views.UsersByRoleView.as_view(), name='users-by-role'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),  # GET profile
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),]