from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
from .models import (
    Course, CourseEnrollment, CourseModule, Lesson, 
    LessonProgress, CourseReview
)

User = get_user_model()


class TeacherSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'profile']
    
    def get_profile(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj)
            return {
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'avatar': profile.avatar,
            }
        except UserProfile.DoesNotExist:
            return {}


class CourseListSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    enrolled_count = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'teacher', 'language',
            'price', 'currency', 'is_free', 'thumbnail_url', 'level',
            'duration_hours', 'category', 'enrolled_count', 'average_rating',
            'is_enrolled', 'created_at'
        ]
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_published=True)
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CourseEnrollment.objects.filter(
                student=request.user, 
                course=obj, 
                is_active=True
            ).exists()
        return False


class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'lesson_type', 'content',
            'video_url', 'duration_minutes', 'order', 'is_free_preview',
            'is_completed'
        ]
    
    def get_is_completed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = LessonProgress.objects.get(student=request.user, lesson=obj)
                return progress.is_completed
            except LessonProgress.DoesNotExist:
                return False
        return False


class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = CourseModule
        fields = ['id', 'title', 'description', 'order', 'lessons']


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)
    enrolled_count = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'teacher', 'language',
            'price', 'currency', 'is_free', 'thumbnail_url', 'level',
            'duration_hours', 'max_students', 'prerequisites', 'learning_objectives',
            'category', 'tags', 'enrolled_count', 'average_rating', 'reviews_count',
            'is_enrolled', 'enrollment_status', 'modules',
            'created_at', 'updated_at'
        ]
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_published=True)
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return 0
    
    def get_reviews_count(self, obj):
        return obj.reviews.filter(is_published=True).count()
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CourseEnrollment.objects.filter(
                student=request.user, 
                course=obj, 
                is_active=True
            ).exists()
        return False
    
    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(student=request.user, course=obj)
                return {
                    'status': enrollment.status,
                    'progress_percentage': float(enrollment.progress_percentage),
                    'enrolled_at': enrollment.enrolled_at
                }
            except CourseEnrollment.DoesNotExist:
                return None
        return None


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'language', 'price', 'currency',
            'is_free', 'thumbnail_url', 'level', 'duration_hours',
            'max_students', 'prerequisites', 'learning_objectives',
            'category', 'tags', 'is_published'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['teacher'] = request.user
        return super().create(validated_data)


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    student = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'enrolled_at', 'status',
            'progress_percentage', 'completed_at'
        ]


class CourseReviewSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseReview
        fields = ['id', 'rating', 'review_text', 'student', 'created_at']
    
    def get_student(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj.student)
            return {
                'name': f"{profile.first_name} {profile.last_name}".strip() or obj.student.email,
                'avatar': profile.avatar
            }
        except UserProfile.DoesNotExist:
            return {'name': obj.student.email, 'avatar': ''}


class CourseReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReview
        fields = ['rating', 'review_text']
    
    def create(self, validated_data):
        request = self.context.get('request')
        course_id = self.context.get('course_id')
        validated_data['student'] = request.user
        validated_data['course_id'] = course_id
        return super().create(validated_data)


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'is_completed', 'completion_percentage',
            'time_spent_minutes', 'started_at', 'completed_at'
        ]


class CourseModuleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order', 'is_published']


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'lesson_type', 'content',
            'video_url', 'duration_minutes', 'order', 'is_published',
            'is_free_preview'
        ]