# Courses API Documentation

## Overview
This document describes the API endpoints for the Courses application in the LMS system.

## Base URL
All endpoints are prefixed with `/api/courses/`

## Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Course Management

#### List/Create Courses
- **GET** `/api/courses/` - List all published courses with filtering and search
- **POST** `/api/courses/` - Create a new course (teachers only)

**Query Parameters for GET:**
- `search` - Search in title, description, category, tags
- `category` - Filter by category
- `level` - Filter by level (beginner, intermediate, advanced, expert)
- `language` - Filter by language
- `price` - Filter by price (free, paid)
- `teacher` - Filter by teacher ID
- `sort` - Sort by (popular, rating, price_low, price_high, -created_at)
- `page` - Page number for pagination
- `page_size` - Number of items per page

**Example:**
```
GET /api/courses/?search=python&level=beginner&sort=popular&page=1
```

#### Course Details
- **GET** `/api/courses/<slug>/` - Get course details
- **PUT** `/api/courses/<slug>/` - Update course (owner/teacher only)
- **DELETE** `/api/courses/<slug>/` - Delete course (owner only)

### 2. Course Enrollment

#### Enroll/Unenroll
- **POST** `/api/courses/<course_id>/enroll/` - Enroll in a course (students only)
- **POST** `/api/courses/<course_id>/unenroll/` - Unenroll from a course

#### My Courses
- **GET** `/api/courses/my/enrolled/` - Get user's enrolled courses
- **GET** `/api/courses/my/teaching/` - Get courses taught by user (teachers only)

### 3. Course Reviews

#### Reviews
- **GET** `/api/courses/<course_id>/reviews/` - Get course reviews
- **POST** `/api/courses/<course_id>/reviews/` - Add a review (enrolled students only)

**POST Body:**
```json
{
    "rating": 5,
    "review_text": "Excellent course!"
}
```

### 4. Wishlist



### 5. Learning Progress

#### Lesson Progress
- **POST** `/api/courses/lessons/<lesson_id>/progress/` - Update lesson progress

**POST Body:**
```json
{
    "completion_percentage": 100,
    "time_spent_minutes": 30,
    "is_completed": true
}
```

### 6. Course Structure



#### Modules
- **GET** `/api/courses/<course_id>/modules/` - Get course modules
- **POST** `/api/courses/<course_id>/modules/` - Create a new module (course owner/teacher only)

#### Module Details
- **GET** `/api/courses/modules/<module_id>/` - Get module details
- **PUT** `/api/courses/modules/<module_id>/` - Update module (course owner/teacher only)
- **DELETE** `/api/courses/modules/<module_id>/` - Delete module (course owner only)

#### Lessons
- **GET** `/api/courses/modules/<module_id>/lessons/` - Get module lessons
- **POST** `/api/courses/modules/<module_id>/lessons/` - Create a new lesson (course owner/teacher only)

## Data Models

### Course
```json
{
    "id": 1,
    "title": "Complete Python Programming Bootcamp",
    "slug": "complete-python-programming-bootcamp",
    "description": "Learn Python from scratch...",
    "teacher": {
        "id": 1,
        "email": "teacher@example.com",
        "profile": {
            "first_name": "John",
            "last_name": "Doe",
            "avatar": "https://example.com/avatar.jpg"
        }
    },
    "language": "en",
    "price": "99.99",
    "currency": "USD",
    "is_free": false,
    "thumbnail_url": "https://example.com/thumbnail.jpg",
    "level": "beginner",
    "duration_hours": 40,
    "max_students": null,
    "prerequisites": "Basic computer skills",
    "learning_objectives": "Master Python fundamentals...",
    "category": "Programming",
    "tags": "python, programming, beginner",
    "enrolled_count": 150,
    "average_rating": 4.5,
    "reviews_count": 45,
    "is_enrolled": false,

    "enrollment_status": null,
    "modules": [...],
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
}
```

### Course Module
```json
{
    "id": 1,
    "title": "Introduction and Setup",
    "description": "Learn about introduction and setup...",
    "order": 1,
    "lessons": [...]
}
```

### Lesson
```json
{
    "id": 1,
    "title": "Lesson 1: Python Installation",
    "description": "Learn how to install Python",
    "lesson_type": "video",
    "content": "This is the lesson content...",
    "video_url": "https://example.com/video.mp4",
    "duration_minutes": 15,
    "order": 1,
    "is_free_preview": true,
    "is_completed": false
}
```

### Course Enrollment
```json
{
    "id": 1,
    "course": {...},
    "student": "student@example.com",
    "enrolled_at": "2023-01-01T00:00:00Z",
    "status": "enrolled",
    "progress_percentage": "25.50",
    "completed_at": null
}
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "Validation error message"
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "error": "Permission denied"
}
```

### 404 Not Found
```json
{
    "error": "Course not found"
}
```

## Permissions

### Student Role
- Can view published courses
- Can enroll/unenroll from courses
- Can add reviews for enrolled courses

- Can track learning progress

### Teacher Role
- All student permissions
- Can create, update, and delete own courses
- Can create modules and lessons for own courses
- Can view teaching analytics

### Admin Role
- All permissions
- Can manage all courses
- Can manage user roles

## Usage Examples

### 1. Get All Courses with Search
```bash
curl -X GET "http://localhost:8000/api/courses/?search=python&level=beginner" \
  -H "Authorization: Bearer your_jwt_token"
```

### 2. Create a New Course
```bash
curl -X POST "http://localhost:8000/api/courses/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Advanced Django Development",
    "description": "Learn advanced Django concepts",
    "level": "advanced",
    "price": 199.99,
    "currency": "USD",
    "language": "en",
    "category": "Web Development",
    "duration_hours": 60,
    "prerequisites": "Python and Django basics",
    "learning_objectives": "Master Django advanced features"
  }'
```

### 3. Enroll in a Course
```bash
curl -X POST "http://localhost:8000/api/courses/1/enroll/" \
  -H "Authorization: Bearer your_jwt_token"
```

### 4. Update Lesson Progress
```bash
curl -X POST "http://localhost:8000/api/courses/lessons/1/progress/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "completion_percentage": 100,
    "time_spent_minutes": 25,
    "is_completed": true
  }'
```

### 5. Add a Course Review
```bash
curl -X POST "http://localhost:8000/api/courses/1/reviews/" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "review_text": "Excellent course! Highly recommended."
  }'
```

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Pagination is available for list endpoints
- File uploads for thumbnails should be handled separately
- Course slugs are automatically generated from titles
- Progress tracking is automatic when lessons are completed
- Course completion is calculated based on lesson completion percentage