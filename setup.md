# LMS Setup Guide

## Prerequisites
- Python 3.8+
- MySQL 8.0+
- Redis (for caching and Celery)

## Setup Steps

### 1. Virtual Environment (✅ Done)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies (✅ Done)
```bash
pip install -r requirements.txt
```

### 3. Database Setup
Create MySQL database:
```sql
CREATE DATABASE LMS CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Environment Configuration (✅ Done)
Update `.env` file with your database credentials:
```
DB_NAME=LMS
DB_USER=your_mysql_user
DB_PASSWORD=DB_PASSWORD
DB_HOST=localhost
DB_PORT=3306
```

### 5. Django Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 6. Optional: Start Background Services
```bash
# Start Redis (if not running)
redis-server

# Start Celery worker (in separate terminal)
source venv/bin/activate
celery -A config worker -l info

# Start Celery beat (in separate terminal)
source venv/bin/activate
celery -A config beat -l info
```

## Project Structure
- Virtual environment: `venv/` (✅ Created)
- Database: MySQL with PyMySQL driver (✅ Configured)
- Apps: authentication, users, core, common (✅ Created)
- Configuration: Django settings, Celery, Redis (✅ Done)