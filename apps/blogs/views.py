from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Blog
from .serializers import (
    BlogListSerializer, BlogDetailSerializer, BlogCreateUpdateSerializer
)


class BlogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


@extend_schema(
    methods=['GET'],
    summary='List blogs',
    description='Get all published blogs with pagination and search',
    parameters=[
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in title, description'),
        OpenApiParameter('category', OpenApiTypes.INT, description='Filter by category ID'),
        OpenApiParameter('tag', OpenApiTypes.INT, description='Filter by tag ID'),
        OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page')
    ],
    responses={200: BlogListSerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Create blog',
    description='Create a new blog post (Authenticated users only)',
    request=BlogCreateUpdateSerializer,
    responses={201: BlogDetailSerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def blogs_list_create(request):
    """
    GET: List all published blogs (Public)
    POST: Create a new blog (Authenticated users only)
    """
    if request.method == 'GET':
        blogs = Blog.objects.filter(is_published=True)
        
        # Search
        search = request.GET.get('search', '')
        if search:
            blogs = blogs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Filter by category
        category_id = request.GET.get('category', '')
        if category_id:
            blogs = blogs.filter(category_id=category_id)
        
        # Filter by tag
        tag_id = request.GET.get('tag', '')
        if tag_id:
            blogs = blogs.filter(tags__id=tag_id)
        
        # Order by published date
        blogs = blogs.order_by('-published_at', '-created_at')
        
        paginator = BlogPagination()
        paginated_blogs = paginator.paginate_queryset(blogs, request)
        serializer = BlogListSerializer(paginated_blogs, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required to create blog posts'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = BlogCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            blog = serializer.save()
            return Response(
                BlogDetailSerializer(blog, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    summary='Get blog details',
    description='Get detailed blog information',
    responses={200: BlogDetailSerializer}
)
@extend_schema(
    methods=['PUT'],
    summary='Update blog',
    description='Update blog (Owner only)',
    request=BlogCreateUpdateSerializer,
    responses={200: BlogDetailSerializer}
)
@extend_schema(
    methods=['DELETE'],
    summary='Delete blog',
    description='Delete blog (Owner or Admin only)',
    responses={204: None}
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def blog_detail(request, id):
    """
    GET: Get blog details (Public for published blogs)
    PUT: Update blog (owner only)
    DELETE: Delete blog (owner or admin only)
    """
    blog = get_object_or_404(Blog, id=id)
    
    if request.method == 'GET':
        if blog.is_published:
            serializer = BlogDetailSerializer(blog, context={'request': request})
            return Response(serializer.data)
        else:
            # Unpublished blogs only accessible by author
            if not request.user.is_authenticated or blog.author != request.user:
                return Response(
                    {'error': 'Blog not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = BlogDetailSerializer(blog, context={'request': request})
            return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if blog.author != request.user:
            return Response(
                {'error': 'Only the author can edit this blog'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BlogCreateUpdateSerializer(
            blog,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            updated_blog = serializer.save()
            return Response(
                BlogDetailSerializer(updated_blog, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Allow deletion by owner OR superuser
        if blog.author != request.user and not request.user.is_superuser:
            return Response(
                {'error': 'Only the author or admin can delete this blog'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        blog.delete()
        return Response(
            {'message': 'Blog deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(
    summary='Get my blogs',
    description='Get blogs created by authenticated user',
    responses={200: BlogListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_blogs(request):
    """Get blogs created by the authenticated user"""
    blogs = Blog.objects.filter(author=request.user).order_by('-created_at')
    
    paginator = BlogPagination()
    paginated_blogs = paginator.paginate_queryset(blogs, request)
    serializer = BlogListSerializer(paginated_blogs, many=True, context={'request': request})
    
    return paginator.get_paginated_response(serializer.data)