from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create admin user'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='dev.maddy.1092@gmail.com',
                password='P@ss1234.&*-'
            )
            self.stdout.write('Superuser created successfully!')
        else:
            self.stdout.write('Superuser already exists!')