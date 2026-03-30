from django.urls import path
from . import views

urlpatterns = [
    # Category URLs
    path('categories/', views.categories_list_create, name='categories-list-create'),
    path('categories/<int:pk>/', views.category_detail, name='category-detail'),
    
    # Course URLs
    path('', views.courses_list_create, name='courses-list-create'),
    path('by-category/', views.courses_by_category, name='courses-by-category'),
    path('<int:id>/', views.course_detail, name='course-detail'),
    
    # Course Reviews
    path('<int:course_id>/reviews/', views.course_reviews, name='course-reviews'),
    
    # Course Modules & Lessons
    path('<int:course_id>/modules/', views.course_modules, name='course-modules'),
    path('modules/<int:module_id>/', views.module_detail, name='module-detail'),
    path('modules/<int:module_id>/lessons/', views.module_lessons, name='module-lessons'),
    
    # Enrollment URLs
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll-course'),
    path('<int:course_id>/unenroll/', views.unenroll_course, name='unenroll-course'),
    path('my-courses/', views.my_courses, name='my-courses'),
    path('my-teaching/', views.my_teaching_courses, name='my-teaching-courses'),
    
    # Lesson Progress
    path('lessons/<int:lesson_id>/progress/', views.update_lesson_progress, name='update-lesson-progress'),
    
    # Contact Support
    # path('contact-support/', views.contact_support, name='contact-support'),
]