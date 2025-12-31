from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.core.models import BaseModel

User = get_user_model()


class Course(BaseModel):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('INR', 'Indian Rupee'),
        ('PKR', 'Pakistani Rupee'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('ur', 'Urdu'),
        ('hi', 'Hindi'),
        ('ar', 'Arabic'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_courses')
    description = models.TextField()
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    is_published = models.BooleanField(default=False)
    thumbnail_url = models.URLField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    
    duration_hours = models.PositiveIntegerField(default=0)
    max_students = models.PositiveIntegerField(null=True, blank=True)
    prerequisites = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    is_free = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Course.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    # REMOVE THE ENROLLED_COUNT PROPERTY COMPLETELY
    # @property
    # def enrolled_count(self):
    #     return self.course_enrollments.filter(is_active=True).count()
    
    @property
    def is_full(self):
        if self.max_students:
            # Calculate directly without using enrolled_count property
            count = self.course_enrollments.filter(is_active=True).count()
            return count >= self.max_students
        return False


class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    is_active = models.BooleanField(default=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title}"


class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    LESSON_TYPES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('live', 'Live Session'),
    ]
    
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_free_preview = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.course.title} - {self.title}"


class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'lesson']
    
    def __str__(self):
        return f"{self.student.email} - {self.lesson.title}"


class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    review_text = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.rating} stars by {self.student.email}"