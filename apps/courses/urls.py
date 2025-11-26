from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course CRUD
    path('', views.courses_list_create, name='courses-list-create'),
    path('<slug:slug>/', views.course_detail, name='course-detail'),
    
    # Course enrollment
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll-course'),
    path('<int:course_id>/unenroll/', views.unenroll_course, name='unenroll-course'),
    
    # User courses
    path('my/enrolled/', views.my_courses, name='my-courses'),
    path('my/teaching/', views.my_teaching_courses, name='my-teaching-courses'),
    
    # Course reviews
    path('<int:course_id>/reviews/', views.course_reviews, name='course-reviews'),
    
    # Lesson progress
    path('lessons/<int:lesson_id>/progress/', views.update_lesson_progress, name='lesson-progress'),
    
    # Course management (for teachers)
    path('<int:course_id>/modules/', views.course_modules, name='course-modules'),
    path('modules/<int:module_id>/', views.module_detail, name='module-detail'),
    path('modules/<int:module_id>/lessons/', views.module_lessons, name='module-lessons'),
]