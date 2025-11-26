from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone
from apps.users.models import UserProfile, Role
from .models import (
    Course, CourseEnrollment, CourseModule, Lesson, 
    LessonProgress, CourseReview
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    CourseEnrollmentSerializer, CourseReviewSerializer, CourseReviewCreateSerializer,
    LessonProgressSerializer, CourseModuleSerializer, CourseModuleCreateUpdateSerializer,
    LessonSerializer, LessonCreateUpdateSerializer
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


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def courses_list_create(request):
    """
    GET: List all published courses with filtering and search
    POST: Create a new course (teachers only)
    """
    if request.method == 'GET':
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
            courses = courses.filter(category__iexact=category)
        
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
            courses = courses.annotate(enrollment_count=Count('course_enrollments')).order_by('-enrollment_count')
        elif sort_by == 'rating':
            courses = courses.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
        elif sort_by == 'price_low':
            courses = courses.order_by('price')
        elif sort_by == 'price_high':
            courses = courses.order_by('-price')
        else:
            courses = courses.order_by(sort_by)
        
        paginator = CoursesPagination()
        paginated_courses = paginator.paginate_queryset(courses, request)
        serializer = CourseListSerializer(paginated_courses, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
        if not is_teacher(request.user):
            return Response(
                {'error': 'Only teachers can create courses'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CourseCreateUpdateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(
                CourseDetailSerializer(course, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def course_detail(request, slug):
    """
    GET: Get course details
    PUT: Update course (teacher only)
    DELETE: Delete course (teacher only)
    """
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'GET':
        # Anyone can view published courses, only teacher can view unpublished
        if not course.is_published and course.teacher != request.user:
            return Response(
                {'error': 'Course not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CourseDetailSerializer(course, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
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
                CourseDetailSerializer(course, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
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


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def course_reviews(request, course_id):
    """
    GET: Get course reviews
    POST: Add a review (enrolled students only)
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'GET':
        reviews = CourseReview.objects.filter(course=course, is_published=True)
        paginator = CoursesPagination()
        paginated_reviews = paginator.paginate_queryset(reviews, request)
        serializer = CourseReviewSerializer(paginated_reviews, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    elif request.method == 'POST':
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
    completion_percentage = request.data.get('completion_percentage', progress.completion_percentage)
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
    total_lessons = Lesson.objects.filter(module__course=lesson.module.course).count()
    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=lesson.module.course,
        is_completed=True
    ).count()
    
    if total_lessons > 0:
        enrollment.progress_percentage = (completed_lessons / total_lessons) * 100
        if enrollment.progress_percentage == 100:
            enrollment.status = 'completed'
            enrollment.completed_at = timezone.now()
        enrollment.save()
    
    serializer = LessonProgressSerializer(progress)
    return Response(serializer.data)





# Course Management Views for Teachers

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def course_modules(request, course_id):
    """
    GET: Get course modules
    POST: Create a new module (course teacher only)
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'GET':
        # Check access permissions
        if not course.is_published and course.teacher != request.user:
            # Check if user is enrolled
            if not CourseEnrollment.objects.filter(
                student=request.user, 
                course=course, 
                is_active=True
            ).exists():
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        modules = CourseModule.objects.filter(course=course, is_published=True)
        serializer = CourseModuleSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if course.teacher != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = CourseModuleCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            module = serializer.save(course=course)
            return Response(
                CourseModuleSerializer(module, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def module_detail(request, module_id):
    """
    GET: Get module details
    PUT: Update module (course teacher only)
    DELETE: Delete module (course teacher only)
    """
    module = get_object_or_404(CourseModule, id=module_id)
    
    if request.method == 'GET':
        # Check access permissions
        if not module.course.is_published and module.course.teacher != request.user:
            if not CourseEnrollment.objects.filter(
                student=request.user, 
                course=module.course, 
                is_active=True
            ).exists():
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = CourseModuleSerializer(module, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
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
                CourseModuleSerializer(module, context={'request': request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
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


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def module_lessons(request, module_id):
    """
    GET: Get module lessons
    POST: Create a new lesson (course teacher only)
    """
    module = get_object_or_404(CourseModule, id=module_id)
    
    if request.method == 'GET':
        # Check access permissions
        if not module.course.is_published and module.course.teacher != request.user:
            if not CourseEnrollment.objects.filter(
                student=request.user, 
                course=module.course, 
                is_active=True
            ).exists():
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        lessons = Lesson.objects.filter(module=module, is_published=True)
        serializer = LessonSerializer(lessons, many=True, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'POST':
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