from django.contrib import admin
from .models import (
    Course, CourseEnrollment, CourseModule, Lesson, 
    LessonProgress, CourseReview
)





class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 0
    fields = ['title', 'order', 'is_published']


class CourseEnrollmentInline(admin.TabularInline):
    model = CourseEnrollment
    extra = 0
    readonly_fields = ['enrolled_at', 'progress_percentage']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'teacher', 'level', 'price', 'currency', 
        # 'is_published', 'is_free', 'enrolled_count', 'created_at'
        'is_published', 'is_free', 'created_at'
    ]
    list_filter = [
        'is_published', 'is_free', 'level', 'language', 
        'currency', 'category', 'created_at'
    ]
    search_fields = ['title', 'description', 'teacher__email', 'category', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    # readonly_fields = ['enrolled_count', 'created_at', 'updated_at']
    inlines = [CourseModuleInline, CourseEnrollmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'tags')
        }),
        ('Course Details', {
            'fields': (
                'teacher', 'level', 'language', 'duration_hours',
                'max_students', 'prerequisites', 'learning_objectives'
            )
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'is_free')
        }),
        ('Media', {
            'fields': ('thumbnail_url',)
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            # 'fields': ('enrolled_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # def enrolled_count(self, obj):
    #     return obj.enrolled_count
    # enrolled_count.short_description = 'Enrolled Students'

    def enrolled_count(self, obj):
        return obj.course_enrollments.filter(is_active=True).count()
    enrolled_count.short_description = 'Enrolled Students'


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ['title', 'lesson_type', 'order', 'duration_minutes', 'is_published', 'is_free_preview']


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published', 'created_at']
    list_filter = ['is_published', 'course', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'module', 'lesson_type', 'order', 
        'duration_minutes', 'is_published', 'is_free_preview'
    ]
    list_filter = [
        'lesson_type', 'is_published', 'is_free_preview', 
        'module__course', 'created_at'
    ]
    search_fields = ['title', 'description', 'module__title', 'module__course__title']


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'status', 'progress_percentage', 
        'is_active', 'enrolled_at', 'completed_at'
    ]
    list_filter = ['status', 'is_active', 'enrolled_at', 'completed_at']
    search_fields = ['student__email', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'lesson', 'is_completed', 'completion_percentage',
        'time_spent_minutes', 'started_at', 'completed_at'
    ]
    list_filter = ['is_completed', 'lesson__lesson_type', 'started_at', 'completed_at']
    search_fields = ['student__email', 'lesson__title', 'lesson__module__course__title']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'rating', 'is_published', 'created_at']
    list_filter = ['rating', 'is_published', 'created_at']
    search_fields = ['course__title', 'student__email', 'review_text']
    readonly_fields = ['created_at', 'updated_at']



