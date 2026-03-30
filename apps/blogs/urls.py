from django.urls import path
from . import views

urlpatterns = [
    path('', views.blogs_list_create, name='blogs-list-create'),
    path('<int:id>/', views.blog_detail, name='blog-detail'),
    path('my-blogs/', views.my_blogs, name='my-blogs'),
]