from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg
from apps.users.models import UserProfile
from .models import (
    Course, Category, CourseEnrollment, CourseModule, Lesson, 
    LessonProgress, CourseReview
)

User = get_user_model()


# ============ CATEGORY SERIALIZERS ============

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'icon_src', 'description', 'is_active', 'created_at', 'updated_at']


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['title', 'icon_src', 'description', 'is_active']


# ============ TEACHER SERIALIZER ============

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


# ============ LESSON SERIALIZERS ============

class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'lesson_type', 'content',
            'video_url', 'duration_minutes', 'order', 'is_free_preview',
            'is_completed', 'is_published', 'created_at', 'updated_at'
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


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'lesson_type', 'content',
            'video_url', 'duration_minutes', 'order', 'is_published',
            'is_free_preview'
        ]


# ============ MODULE SERIALIZERS ============

class CourseModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = CourseModule
        fields = ['id', 'title', 'order', 'description', 
                 'is_published', 'created_at', 'updated_at', 'lessons']


class CourseModuleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseModule
        fields = ['title', 'description', 'order', 'is_published']


# ============ COURSE LIST SERIALIZER ============

class CourseListSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    teacher_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    modules = CourseModuleSerializer(many=True, read_only=True)
    total_lessons_duration_minutes = serializers.SerializerMethodField()
    total_lessons_duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'teacher', 'teacher_name', 'language',
            'price', 'currency', 'is_free', 'thumbnail_url', 'level',
            'duration_hours', 'categories', 'category_ids', 'average_rating',
            'is_enrolled', 'created_at', 'is_published', 'tags', 'modules', 
            'total_lessons_duration_minutes', 'total_lessons_duration_hours',
        ]
    
    def get_average_rating(self, obj):
        try:
            result = obj.reviews.filter(is_published=True).aggregate(
                average=Avg('rating')
            )
            avg = result.get('average')
            if avg is not None:
                return round(float(avg), 1)
            return 0.0
        except Exception:
            return 0.0
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.course_enrollments.filter(
                    student=request.user, 
                    is_active=True
                ).exists()
            except Exception:
                return False
        return False
    
    def get_teacher_name(self, obj):
        if obj.teacher:
            try:
                profile = UserProfile.objects.get(user=obj.teacher)
                full_name = f"{profile.first_name} {profile.last_name}".strip()
                if full_name:
                    return full_name
            except UserProfile.DoesNotExist:
                pass
        return obj.teacher.email if obj.teacher else ""

    def get_total_lessons_duration_minutes(self, obj):
        if hasattr(obj, 'modules'):
            total = 0
            for module in obj.modules.all():
                if module.is_published:
                    for lesson in module.lessons.all():
                        if lesson.is_published:
                            total += lesson.duration_minutes or 0
            return total
        return 0

    def get_total_lessons_duration_hours(self, obj):
        minutes = self.get_total_lessons_duration_minutes(obj)
        if minutes:
            return round(minutes / 60, 1)
        return 0


# ============ COURSE DETAIL SERIALIZER ============

class CourseDetailSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)
    teacher_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    total_lessons_duration_minutes = serializers.SerializerMethodField()
    total_lessons_duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'teacher', 'teacher_name', 'language',
            'price', 'currency', 'is_free', 'thumbnail_url', 'level',
            'duration_hours', 'max_students', 'prerequisites', 'learning_objectives',
            'categories', 'tags', 'average_rating', 'reviews_count',
            'is_enrolled', 'enrollment_status', 'modules',
            'created_at', 'updated_at', 'is_published', 
            'total_lessons_duration_minutes', 'total_lessons_duration_hours',
        ]
    
    def get_average_rating(self, obj):
        try:
            result = obj.reviews.filter(is_published=True).aggregate(
                average=Avg('rating')
            )
            avg = result.get('average')
            if avg is not None:
                return round(float(avg), 1)
            return 0.0
        except Exception:
            return 0.0
    
    def get_reviews_count(self, obj):
        try:
            return obj.reviews.filter(is_published=True).count()
        except Exception:
            return 0
    
    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.course_enrollments.filter(
                    student=request.user, 
                    is_active=True
                ).exists()
            except Exception:
                return False
        return False
    
    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = CourseEnrollment.objects.get(student=request.user, course=obj)
                return {
                    'status': enrollment.status,
                    'progress_percentage': float(enrollment.progress_percentage),
                    'enrolled_at': enrollment.enrolled_at,
                    'is_active': enrollment.is_active
                }
            except CourseEnrollment.DoesNotExist:
                return None
        return None
    
    def get_teacher_name(self, obj):
        if obj.teacher:
            try:
                profile = UserProfile.objects.get(user=obj.teacher)
                full_name = f"{profile.first_name} {profile.last_name}".strip()
                if full_name:
                    return full_name
            except UserProfile.DoesNotExist:
                pass
        return obj.teacher.email if obj.teacher else ""

    def get_total_lessons_duration_minutes(self, obj):
        if hasattr(obj, 'modules'):
            total = 0
            for module in obj.modules.all():
                if module.is_published:
                    for lesson in module.lessons.all():
                        if lesson.is_published:
                            total += lesson.duration_minutes or 0
            return total
        return 0

    def get_total_lessons_duration_hours(self, obj):
        minutes = self.get_total_lessons_duration_minutes(obj)
        if minutes:
            return round(minutes / 60, 1)
        return 0


# ============ COURSE CREATE/UPDATE SERIALIZER ============

class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'language', 'price', 'currency',
            'is_free', 'thumbnail_url', 'level', 'duration_hours',
            'max_students', 'prerequisites', 'learning_objectives',
            'category_ids', 'tags', 'is_published'
        ]
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        request = self.context.get('request')
        validated_data['teacher'] = request.user
        course = super().create(validated_data)
        course.categories.set(category_ids)
        return course
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        course = super().update(instance, validated_data)
        if category_ids is not None:
            course.categories.set(category_ids)
        return course


# ============ ENROLLMENT SERIALIZER ============

class CourseEnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    student = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'enrolled_at', 'status',
            'progress_percentage', 'completed_at', 'is_active'
        ]


# ============ REVIEW SERIALIZERS ============

class CourseReviewSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseReview
        fields = ['id', 'rating', 'review_text', 'student', 'student_name', 'created_at']
    
    def get_student(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj.student)
            return {
                'id': obj.student.id,
                'email': obj.student.email,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'avatar': profile.avatar
            }
        except UserProfile.DoesNotExist:
            return {
                'id': obj.student.id,
                'email': obj.student.email,
                'first_name': '',
                'last_name': '',
                'avatar': ''
            }
    
    def get_student_name(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj.student)
            full_name = f"{profile.first_name} {profile.last_name}".strip()
            if full_name:
                return full_name
        except UserProfile.DoesNotExist:
            pass
        return obj.student.email


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


# ============ PROGRESS SERIALIZER ============

class LessonProgressSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'lesson', 'is_completed', 'completion_percentage',
            'time_spent_minutes', 'started_at', 'completed_at'
        ]


# ============ CONTACT SUPPORT SERIALIZER ============

class ContactSupportSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    message = serializers.CharField(max_length=2000)
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long")
        return value