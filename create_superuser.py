#!/usr/bin/env python
import os
import django
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='dev.maddy.1092@gmail.com',
        password='P@ss1234.&*-'
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists!')