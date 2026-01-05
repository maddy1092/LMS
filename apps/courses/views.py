from django.db import models
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from apps.users.models import UserProfile, Role
from .models import (
    Course, CourseEnrollment, CourseModule, Lesson, Category,
    LessonProgress, CourseReview
)
from .serializers import (
    CourseListSerializer, CategorySerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    CourseEnrollmentSerializer, CourseReviewSerializer, CourseReviewCreateSerializer,
    LessonProgressSerializer, CourseModuleSerializer, CourseModuleCreateUpdateSerializer,
    LessonSerializer, LessonCreateUpdateSerializer, CategoryCreateUpdateSerializer
)


class CoursesPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


def is_teacher(user):
    """Check if user has teacher role"""
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role and profile.role.name == 'Teacher'
    except UserProfile.DoesNotExist:
        return False


def is_student(user):
    """Check if user has student role"""
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role and profile.role.name == 'Student'
    except UserProfile.DoesNotExist:
        return False


# ============ PUBLIC VIEWS ============

# Category views
@extend_schema(
    methods=['GET'],
    summary='List categories',
    description='Get all active categories with course counts',
    responses={200: CategorySerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Create category',
    description='Create a new category (Admin only)',
    request=CategoryCreateUpdateSerializer,
    responses={201: CategorySerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def categories_list_create(request):
    """
    GET: List all active categories with course counts (Public)
    POST: Create a new category (Admin only)
    """
    if request.method == 'GET':
        categories = Category.objects.filter(is_active=True).annotate(
            courses_count=Count('courses', filter=Q(courses__is_published=True))
        )
        
        data = []
        for category in categories:
            data.append({
                'id': category.id,
                'title': category.title,
                'icon_src': category.icon_src,
                'description': category.description,
                'is_active': category.is_active,
                'courses_count': category.courses_count,
                'created_at': category.created_at,
                'updated_at': category.updated_at
            })
        
        return Response(data)
    
    elif request.method == 'POST':
        # Only admin can create categories
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response(
                {'error': 'Only admin can create categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CategoryCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(
                CategorySerializer(category).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    summary='Get category details',
    description='Get category details (Public)',
    responses={200: CategorySerializer}
)
@extend_schema(
    methods=['PUT'],
    summary='Update category',
    description='Update category (Admin only)',
    request=CategoryCreateUpdateSerializer,
    responses={200: CategorySerializer}
)
@extend_schema(
    methods=['DELETE'],
    summary='Delete category',
    description='Delete category (Admin only)',
    responses={204: None}
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def category_detail(request, pk):
    """
    GET: Get category details (Public)
    PUT: Update category (Admin only)
    DELETE: Delete category (Admin only)
    """
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response(
                {'error': 'Only admin can update categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CategoryCreateUpdateSerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            category = serializer.save()
            return Response(CategorySerializer(category).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response(
                {'error': 'Only admin can delete categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        category.delete()
        return Response(
            {'message': 'Category deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )

@extend_schema(
    methods=['GET'],
    summary='List courses',
    description='Get all published courses with filtering and search',
    parameters=[
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in title, description, tags'),
        OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category name'),
        OpenApiParameter('level', OpenApiTypes.STR, description='Filter by level'),
        OpenApiParameter('language', OpenApiTypes.STR, description='Filter by language'),
        OpenApiParameter('price', OpenApiTypes.STR, description='Filter by price: free or paid'),
        OpenApiParameter('teacher', OpenApiTypes.INT, description='Filter by teacher ID'),
        OpenApiParameter('sort', OpenApiTypes.STR, description='Sort by: popular, rating, price_low, price_high, -created_at'),
        OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page')
    ],
    responses={200: CourseListSerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Create course',
    description='Create a new course (Teachers only)',
    request=CourseCreateUpdateSerializer,
    responses={201: CourseDetailSerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def courses_list_create(request):
    """
    GET: List all published courses with filtering and search (Public)
    POST: Create a new course (teachers only)
    """
    if request.method == 'GET':
        try:
            # Public access - no authentication required
            courses = Course.objects.filter(is_published=True)

            # Search functionality
            search = request.GET.get('search', '')
            if search:
                courses = courses.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(category__icontains=search) |
                    Q(tags__icontains=search)
                )

            # Filter by category
            category = request.GET.get('category', '')
            if category:
                courses = courses.filter(categories__title__iexact=category_name)

            # Filter by level
            level = request.GET.get('level', '')
            if level:
                courses = courses.filter(level=level)

            # Filter by language
            language = request.GET.get('language', '')
            if language:
                courses = courses.filter(language=language)

            # Filter by price
            price_filter = request.GET.get('price', '')
            if price_filter == 'free':
                courses = courses.filter(is_free=True)
            elif price_filter == 'paid':
                courses = courses.filter(is_free=False)

            # Filter by teacher
            teacher_id = request.GET.get('teacher', '')
            if teacher_id:
                courses = courses.filter(teacher_id=teacher_id)

            # Sorting - FIXED: Use try-except for annotations
            sort_by = request.GET.get('sort', '-created_at')

            if sort_by == 'popular':
                try:
                    courses = courses.annotate(
                        enrollment_count=models.Count('course_enrollments')
                    ).order_by('-enrollment_count')
                except Exception:
                    courses = courses.order_by('-created_at')
                    
            elif sort_by == 'rating':
                try:
                    courses = courses.annotate(
                        avg_rating=models.Avg('reviews__rating')
                    ).order_by('-avg_rating')
                except Exception:
                    courses = courses.order_by('-created_at')
                    
            elif sort_by == 'price_low':
                courses = courses.order_by('price')
            elif sort_by == 'price_high':
                courses = courses.order_by('-price')
            else:
                courses = courses.order_by(sort_by)

            paginator = CoursesPagination()
            paginated_courses = paginator.paginate_queryset(courses, request)
            
            # Use serializer with context but no complex calculations initially
            serializer = CourseListSerializer(
                paginated_courses, many=True, context={'request': request})
            
            return paginator.get_paginated_response(serializer.data)
            
        except Exception as e:
            # Return error response if something goes wrong
            return Response(
                {'error': str(e), 'detail': 'An error occurred while fetching courses'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        # POST requires authentication - check manually
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
        if not is_teacher(request.user):
            return Response(
                {'error': 'Only teachers can create courses'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CourseCreateUpdateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(
                CourseDetailSerializer(
                    course, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary='Get courses by category',
    description='Get published courses by category/categories',
    parameters=[
        OpenApiParameter('category', OpenApiTypes.STR, required=True, description='Single category or comma-separated categories'),
        OpenApiParameter('search', OpenApiTypes.STR, description='Search in title, description, tags'),
        OpenApiParameter('level', OpenApiTypes.STR, description='Filter by level'),
        OpenApiParameter('language', OpenApiTypes.STR, description='Filter by language'),
        OpenApiParameter('price', OpenApiTypes.STR, description='Filter by price: free or paid'),
        OpenApiParameter('teacher', OpenApiTypes.INT, description='Filter by teacher ID'),
        OpenApiParameter('sort', OpenApiTypes.STR, description='Sort by: popular, rating, price_low, price_high, -created_at'),
        OpenApiParameter('page', OpenApiTypes.INT, description='Page number'),
        OpenApiParameter('page_size', OpenApiTypes.INT, description='Items per page')
    ],
    responses={200: CourseListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def courses_by_category(request):
    """
    GET: Get published courses by category/categories
    Accepts: 
        - Single category: ?category=web-development
        - Multiple categories: ?category=web-development,programming,business
    Returns: Paginated list of published courses matching the categories
    """
    try:
        # Get category parameter from query string
        category_param = request.GET.get('category', '')
        
        if not category_param:
            return Response(
                {'error': 'Category parameter is required. Use ?category=category-slug'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Split by comma to handle multiple categories
        category_slugs = [slug.strip() for slug in category_param.split(',') if slug.strip()]
        
        # Get categories that exist and are active
        categories = Category.objects.filter(
            title__in=category_slugs,
            is_active=True
        )
        
        if not categories.exists():
            return Response(
                {'error': 'No valid categories found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Start with all published courses
        courses = Course.objects.filter(is_published=True)
        
        # Filter by categories - adjust field name based on your model
        # If ForeignKey: courses.filter(category__in=categories)
        # If ManyToMany: courses.filter(categories__in=categories).distinct()
        courses = courses.filter(categories__in=categories).distinct()
        
        # Search functionality
        search = request.GET.get('search', '')
        if search:
            courses = courses.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Filter by level
        level = request.GET.get('level', '')
        if level:
            courses = courses.filter(level=level)
        
        # Filter by language
        language = request.GET.get('language', '')
        if language:
            courses = courses.filter(language=language)
        
        # Filter by price
        price_filter = request.GET.get('price', '')
        if price_filter == 'free':
            courses = courses.filter(is_free=True)
        elif price_filter == 'paid':
            courses = courses.filter(is_free=False)
        
        # Filter by teacher
        teacher_id = request.GET.get('teacher', '')
        if teacher_id:
            courses = courses.filter(teacher_id=teacher_id)
        
        # Sorting
        sort_by = request.GET.get('sort', '-created_at')
        
        if sort_by == 'popular':
            try:
                courses = courses.annotate(
                    enrollment_count=Count('course_enrollments')
                ).order_by('-enrollment_count')
            except Exception:
                courses = courses.order_by('-created_at')
        elif sort_by == 'rating':
            try:
                courses = courses.annotate(
                    avg_rating=models.Avg('reviews__rating')
                ).order_by('-avg_rating')
            except Exception:
                courses = courses.order_by('-created_at')
        elif sort_by == 'price_low':
            courses = courses.order_by('price')
        elif sort_by == 'price_high':
            courses = courses.order_by('-price')
        else:
            courses = courses.order_by(sort_by)
        
        # Prepare response data
        categories_data = []
        for cat in categories:
            categories_data.append({
                'id': cat.id,
                'title': cat.title,
                'icon_src': cat.icon_src,
                'description': cat.description
            })
        
        # Pagination
        paginator = CoursesPagination()
        paginated_courses = paginator.paginate_queryset(courses, request)
        
        # Serialize courses
        serializer = CourseListSerializer(
            paginated_courses,
            many=True,
            context={'request': request}
        )
        
        # Build response
        response_data = {
            'categories': categories_data,
            'courses': serializer.data,
            'filters': {
                'category': category_param,
                'search': search,
                'level': level,
                'language': language,
                'price': price_filter,
                'sort': sort_by
            },
            'pagination': {
                'count': paginator.page.paginator.count,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'current_page': paginator.page.number,
                'total_pages': paginator.page.paginator.num_pages,
                'page_size': paginator.get_page_size(request)
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': str(e), 'detail': 'An error occurred while fetching courses'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    methods=['GET'],
    summary='Get course details',
    description='Get detailed course information',
    responses={200: CourseDetailSerializer}
)
@extend_schema(
    methods=['PUT'],
    summary='Update course',
    description='Update course (Teacher only)',
    request=CourseCreateUpdateSerializer,
    responses={200: CourseDetailSerializer}
)
@extend_schema(
    methods=['DELETE'],
    summary='Delete course',
    description='Delete course (Teacher only)',
    responses={204: None}
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def course_detail(request, slug):
    """
    GET: Get course details (Public)
    PUT: Update course (teacher only)
    DELETE: Delete course (teacher only)
    """
    course = get_object_or_404(Course, title=slug)

    if request.method == 'GET':
        # Anyone can view published courses
        if course.is_published:
            serializer = CourseDetailSerializer(
                course, context={'request': request})
            return Response(serializer.data)
        else:
            # Unpublished courses only accessible by teacher
            if not request.user or not request.user.is_authenticated or course.teacher != request.user:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = CourseDetailSerializer(
                course, context={'request': request})
            return Response(serializer.data)

    elif request.method == 'PUT':
        # PUT requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if course.teacher != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CourseCreateUpdateSerializer(
            course,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            course = serializer.save()
            return Response(
                CourseDetailSerializer(
                    course, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # DELETE requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if course.teacher != request.user:
            return Response(
                {'error': 'Only course teacher can delete the course'},
                status=status.HTTP_403_FORBIDDEN
            )

        course.delete()
        return Response(
            {'message': 'Course deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(
    methods=['GET'],
    summary='Get course reviews',
    description='Get published reviews for a course',
    responses={200: CourseReviewSerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Add course review',
    description='Add a review (Enrolled students only)',
    request=CourseReviewCreateSerializer,
    responses={201: CourseReviewSerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def course_reviews(request, course_id):
    """
    GET: Get course reviews (Public)
    POST: Add a review (enrolled students only)
    """
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'GET':
        # GET is public - no authentication required
        reviews = CourseReview.objects.filter(course=course, is_published=True)
        paginator = CoursesPagination()
        paginated_reviews = paginator.paginate_queryset(reviews, request)
        serializer = CourseReviewSerializer(paginated_reviews, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == 'POST':
        # POST requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is enrolled
        if not CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            is_active=True
        ).exists():
            return Response(
                {'error': 'You must be enrolled to review this course'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if already reviewed
        if CourseReview.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'error': 'You have already reviewed this course'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CourseReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'course_id': course_id}
        )
        if serializer.is_valid():
            review = serializer.save()
            return Response(
                CourseReviewSerializer(review).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    summary='Get course modules',
    description='Get modules for a course',
    responses={200: CourseModuleSerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Create course module',
    description='Create a new module (Course teacher only)',
    request=CourseModuleCreateUpdateSerializer,
    responses={201: CourseModuleSerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def course_modules(request, course_id):
    """
    GET: Get course modules (Public for published courses)
    POST: Create a new module (course teacher only)
    """
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'GET':
        # Public access for published courses
        if course.is_published:
            modules = CourseModule.objects.filter(
                course=course, is_published=True)
            serializer = CourseModuleSerializer(
                modules, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            # For unpublished courses, check if user is teacher or enrolled
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if course.teacher == request.user:
                modules = CourseModule.objects.filter(course=course)
                serializer = CourseModuleSerializer(
                    modules, many=True, context={'request': request})
                return Response(serializer.data)

            # Check if user is enrolled
            if CourseEnrollment.objects.filter(
                student=request.user,
                course=course,
                is_active=True
            ).exists():
                modules = CourseModule.objects.filter(
                    course=course, is_published=True)
                serializer = CourseModuleSerializer(
                    modules, many=True, context={'request': request})
                return Response(serializer.data)

            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

    elif request.method == 'POST':
        # POST requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if course.teacher != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CourseModuleCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            module = serializer.save(course=course)
            return Response(
                CourseModuleSerializer(
                    module, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    methods=['GET'],
    summary='Get module details',
    description='Get module details with lessons',
    responses={200: CourseModuleSerializer}
)
@extend_schema(
    methods=['PUT'],
    summary='Update module',
    description='Update module (Course teacher only)',
    request=CourseModuleCreateUpdateSerializer,
    responses={200: CourseModuleSerializer}
)
@extend_schema(
    methods=['DELETE'],
    summary='Delete module',
    description='Delete module (Course teacher only)',
    responses={204: None}
)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def module_detail(request, module_id):
    """
    GET: Get module details (Public for published courses)
    PUT: Update module (course teacher only)
    DELETE: Delete module (course teacher only)
    """
    module = get_object_or_404(CourseModule, id=module_id)

    if request.method == 'GET':
        # Public access if course and module are published
        if module.course.is_published and module.is_published:
            serializer = CourseModuleSerializer(
                module, context={'request': request})
            return Response(serializer.data)
        else:
            # Check access permissions
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if module.course.teacher == request.user:
                serializer = CourseModuleSerializer(
                    module, context={'request': request})
                return Response(serializer.data)

            # Check if user is enrolled
            if CourseEnrollment.objects.filter(
                student=request.user,
                course=module.course,
                is_active=True
            ).exists() and module.is_published:
                serializer = CourseModuleSerializer(
                    module, context={'request': request})
                return Response(serializer.data)

            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

    elif request.method == 'PUT':
        # PUT requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if module.course.teacher != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CourseModuleCreateUpdateSerializer(
            module,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            module = serializer.save()
            return Response(
                CourseModuleSerializer(
                    module, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # DELETE requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if module.course.teacher != request.user:
            return Response(
                {'error': 'Only course teacher can delete modules'},
                status=status.HTTP_403_FORBIDDEN
            )

        module.delete()
        return Response(
            {'message': 'Module deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(
    methods=['GET'],
    summary='Get module lessons',
    description='Get lessons for a module',
    responses={200: LessonSerializer(many=True)}
)
@extend_schema(
    methods=['POST'],
    summary='Create lesson',
    description='Create a new lesson (Course teacher only)',
    request=LessonCreateUpdateSerializer,
    responses={201: LessonSerializer}
)
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def module_lessons(request, module_id):
    """
    GET: Get module lessons (Public for published courses)
    POST: Create a new lesson (course teacher only)
    """
    module = get_object_or_404(CourseModule, id=module_id)

    if request.method == 'GET':
        # Public access if course and module are published
        if module.course.is_published and module.is_published:
            lessons = Lesson.objects.filter(module=module, is_published=True)
            serializer = LessonSerializer(
                lessons, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            # Check access permissions
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'detail': 'Authentication credentials were not provided.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if module.course.teacher == request.user:
                lessons = Lesson.objects.filter(module=module)
                serializer = LessonSerializer(
                    lessons, many=True, context={'request': request})
                return Response(serializer.data)

            # Check if user is enrolled
            if CourseEnrollment.objects.filter(
                student=request.user,
                course=module.course,
                is_active=True
            ).exists() and module.is_published:
                lessons = Lesson.objects.filter(
                    module=module, is_published=True)
                serializer = LessonSerializer(
                    lessons, many=True, context={'request': request})
                return Response(serializer.data)

            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )

    elif request.method == 'POST':
        # POST requires authentication
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if module.course.teacher != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = LessonCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            lesson = serializer.save(module=module)
            return Response(
                LessonSerializer(lesson, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============ PRIVATE VIEWS ============

@extend_schema(
    summary='Enroll in course',
    description='Enroll in a course (Students only)',
    responses={201: CourseEnrollmentSerializer}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_course(request, course_id):
    """Enroll in a course"""
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    if not is_student(request.user):
        return Response(
            {'error': 'Only students can enroll in courses'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if already enrolled
    if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
        return Response(
            {'error': 'Already enrolled in this course'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if course is full
    if course.is_full:
        return Response(
            {'error': 'Course is full'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    enrollment = CourseEnrollment.objects.create(
        student=request.user,
        course=course
    )
    
    serializer = CourseEnrollmentSerializer(enrollment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Unenroll from course',
    description='Unenroll from a course',
    responses={200: OpenApiResponse(description='Successfully unenrolled')}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unenroll_course(request, course_id):
    """Unenroll from a course"""
    course = get_object_or_404(Course, id=course_id)
    
    try:
        enrollment = CourseEnrollment.objects.get(student=request.user, course=course)
        enrollment.is_active = False
        enrollment.status = 'dropped'
        enrollment.save()
        
        return Response(
            {'message': 'Successfully unenrolled from course'}, 
            status=status.HTTP_200_OK
        )
    except CourseEnrollment.DoesNotExist:
        return Response(
            {'error': 'Not enrolled in this course'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary='Get my enrolled courses',
    description='Get user enrolled courses',
    responses={200: CourseEnrollmentSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_courses(request):
    """Get user's enrolled courses"""
    enrollments = CourseEnrollment.objects.filter(
        student=request.user, 
        is_active=True
    ).select_related('course')
    
    paginator = CoursesPagination()
    paginated_enrollments = paginator.paginate_queryset(enrollments, request)
    serializer = CourseEnrollmentSerializer(paginated_enrollments, many=True)
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    summary='Get my teaching courses',
    description='Get courses taught by the user (Teachers only)',
    responses={200: CourseListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_teaching_courses(request):
    """Get courses taught by the user"""
    if not is_teacher(request.user):
        return Response(
            {'error': 'Only teachers can access this endpoint'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    courses = Course.objects.filter(teacher=request.user)
    
    paginator = CoursesPagination()
    paginated_courses = paginator.paginate_queryset(courses, request)
    serializer = CourseListSerializer(paginated_courses, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    summary='Update lesson progress',
    description='Update lesson progress (Enrolled students only)',
    request={
        'type': 'object',
        'properties': {
            'completion_percentage': {'type': 'integer', 'description': 'Completion percentage (0-100)'},
            'time_spent_minutes': {'type': 'integer', 'description': 'Time spent in minutes'},
            'is_completed': {'type': 'boolean', 'description': 'Mark as completed'}
        }
    },
    responses={200: LessonProgressSerializer}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_lesson_progress(request, lesson_id):
    """Update lesson progress"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Check if user is enrolled in the course
    if not CourseEnrollment.objects.filter(
        student=request.user,
        course=lesson.module.course,
        is_active=True
    ).exists():
        return Response(
            {'error': 'You must be enrolled to access this lesson'},
            status=status.HTTP_403_FORBIDDEN
        )

    progress, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson
    )

    # Update progress
    completion_percentage = request.data.get(
        'completion_percentage', progress.completion_percentage)
    time_spent = request.data.get('time_spent_minutes', 0)
    is_completed = request.data.get('is_completed', False)

    progress.completion_percentage = completion_percentage
    progress.time_spent_minutes += int(time_spent)

    if is_completed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()

    progress.save()

    # Update course enrollment progress
    enrollment = CourseEnrollment.objects.get(
        student=request.user,
        course=lesson.module.course
    )

    # Calculate overall course progress
    total_lessons = Lesson.objects.filter(
        module__course=lesson.module.course).count()
    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=lesson.module.course,
        is_completed=True
    ).count()

    if total_lessons > 0:
        enrollment.progress_percentage = (
            completed_lessons / total_lessons) * 100
        if enrollment.progress_percentage == 100:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
        enrollment.save()

    serializer = LessonProgressSerializer(progress)
    return Response(serializer.data)