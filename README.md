# Learning Management System (LMS)

A Django-based Learning Management System with REST API support.

## Features

- User authentication and authorization
- Course management
- Lesson management
- Student enrollment
- Progress tracking
- Admin interface
- REST API endpoints
- Background task processing with Celery

## Project Structure

```
LMS/
├── apps/
│   ├── authentication/    # User authentication
│   ├── common/           # Shared utilities
│   ├── core/            # Core LMS models (Course, Lesson, Enrollment)
│   └── users/           # User management
├── config/              # Django settings and configuration
├── media/              # User uploaded files
├── static/             # Static files
├── templates/          # HTML templates
└── logs/              # Application logs
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd LMS
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Environment Variables

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `REDIS_URL`: Redis URL for caching
- `CELERY_BROKER_URL`: Celery broker URL
- `EMAIL_*`: Email configuration

## API Endpoints

- `/admin/` - Django admin interface
- `/api/auth/` - Authentication endpoints
- `/api/users/` - User management endpoints

## Background Tasks

Start Celery worker:
```bash
celery -A config worker -l info
```

Start Celery beat (for scheduled tasks):
```bash
celery -A config beat -l info
```

## Development

- Follow Django best practices
- Use proper error handling
- Write tests for new features
- Update documentation