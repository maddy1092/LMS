from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.models import Role, UserProfile
from apps.courses.models import Course, CourseModule, Lesson
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with sample courses data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample courses data...')
        

        
        # Get or create teacher role
        teacher_role, _ = Role.objects.get_or_create(name='Teacher')
        student_role, _ = Role.objects.get_or_create(name='Student')
        
        # Create sample teachers
        teachers_data = [
            {'email': 'john.doe@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'email': 'jane.smith@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'email': 'mike.johnson@example.com', 'first_name': 'Mike', 'last_name': 'Johnson'},
            {'email': 'sarah.wilson@example.com', 'first_name': 'Sarah', 'last_name': 'Wilson'},
        ]
        
        teachers = []
        for teacher_data in teachers_data:
            user, created = User.objects.get_or_create(
                email=teacher_data['email'],
                defaults={'is_active': True}
            )
            if created:
                user.set_password('password123')
                user.save()
                
                # Create profile
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': teacher_data['first_name'],
                        'last_name': teacher_data['last_name'],
                        'role': teacher_role
                    }
                )
                self.stdout.write(f'Created teacher: {user.email}')
            teachers.append(user)
        
        # Sample courses data
        courses_data = [
            {
                'title': 'Complete Python Programming Bootcamp',
                'description': 'Learn Python from scratch with hands-on projects and real-world applications.',
                'category': 'Programming',
                'level': 'beginner',
                'price': 99.99,
                'duration_hours': 40,
                'language': 'en',
                'tags': 'python, programming, beginner, bootcamp',
                'learning_objectives': 'Master Python fundamentals, Build real projects, Understand OOP concepts',
                'prerequisites': 'Basic computer skills',
            },
            {
                'title': 'React.js Complete Course',
                'description': 'Master React.js and build modern web applications with hooks, context, and more.',
                'category': 'Web Development',
                'level': 'intermediate',
                'price': 129.99,
                'duration_hours': 35,
                'language': 'en',
                'tags': 'react, javascript, frontend, web development',
                'learning_objectives': 'Build React applications, Use hooks and context, State management',
                'prerequisites': 'HTML, CSS, JavaScript basics',
            },
            {
                'title': 'Data Science with Python',
                'description': 'Complete data science course covering pandas, numpy, matplotlib, and machine learning.',
                'category': 'Data Science',
                'level': 'intermediate',
                'price': 149.99,
                'duration_hours': 50,
                'language': 'en',
                'tags': 'data science, python, machine learning, pandas',
                'learning_objectives': 'Data analysis, Machine learning, Data visualization',
                'prerequisites': 'Python basics, Statistics knowledge',
            },
            {
                'title': 'Mobile App Development with Flutter',
                'description': 'Build cross-platform mobile apps using Flutter and Dart programming language.',
                'category': 'Mobile Development',
                'level': 'intermediate',
                'price': 119.99,
                'duration_hours': 45,
                'language': 'en',
                'tags': 'flutter, dart, mobile development, cross-platform',
                'learning_objectives': 'Build mobile apps, Flutter widgets, State management',
                'prerequisites': 'Programming basics, OOP concepts',
            },
            {
                'title': 'UI/UX Design Fundamentals',
                'description': 'Learn the principles of user interface and user experience design.',
                'category': 'Design',
                'level': 'beginner',
                'price': 79.99,
                'duration_hours': 25,
                'language': 'en',
                'tags': 'ui, ux, design, figma, prototyping',
                'learning_objectives': 'Design principles, User research, Prototyping',
                'prerequisites': 'None',
            },
            {
                'title': 'DevOps with Docker and Kubernetes',
                'description': 'Master containerization and orchestration with Docker and Kubernetes.',
                'category': 'DevOps',
                'level': 'advanced',
                'price': 179.99,
                'duration_hours': 60,
                'language': 'en',
                'tags': 'devops, docker, kubernetes, containers',
                'learning_objectives': 'Container deployment, Orchestration, CI/CD pipelines',
                'prerequisites': 'Linux basics, Cloud computing knowledge',
            },
            {
                'title': 'Digital Marketing Masterclass',
                'description': 'Complete guide to digital marketing including SEO, social media, and PPC.',
                'category': 'Marketing',
                'level': 'beginner',
                'price': 89.99,
                'duration_hours': 30,
                'language': 'en',
                'tags': 'digital marketing, seo, social media, ppc',
                'learning_objectives': 'SEO optimization, Social media marketing, PPC campaigns',
                'prerequisites': 'Basic computer skills',
            },
            {
                'title': 'Free Introduction to Programming',
                'description': 'A free course to get started with programming concepts and logic.',
                'category': 'Programming',
                'level': 'beginner',
                'price': 0.00,
                'duration_hours': 15,
                'language': 'en',
                'tags': 'programming, beginner, free, introduction',
                'learning_objectives': 'Programming logic, Problem solving, Basic concepts',
                'prerequisites': 'None',
                'is_free': True,
            },
        ]
        
        # Create courses
        for i, course_data in enumerate(courses_data):
            teacher = teachers[i % len(teachers)]
            
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'description': course_data['description'],
                    'teacher': teacher,
                    'level': course_data['level'],
                    'price': course_data['price'],
                    'duration_hours': course_data['duration_hours'],
                    'language': course_data['language'],
                    'category': course_data['category'],
                    'tags': course_data['tags'],
                    'learning_objectives': course_data['learning_objectives'],
                    'prerequisites': course_data['prerequisites'],
                    'is_free': course_data.get('is_free', False),
                    'is_published': True,
                }
            )
            
            if created:
                self.stdout.write(f'Created course: {course.title}')
                
                # Create modules for each course
                modules_data = [
                    {'title': 'Introduction and Setup', 'order': 1},
                    {'title': 'Core Concepts', 'order': 2},
                    {'title': 'Practical Applications', 'order': 3},
                    {'title': 'Advanced Topics', 'order': 4},
                    {'title': 'Final Project', 'order': 5},
                ]
                
                for module_data in modules_data:
                    module = CourseModule.objects.create(
                        course=course,
                        title=module_data['title'],
                        description=f"Learn about {module_data['title'].lower()} in {course.title}",
                        order=module_data['order'],
                        is_published=True
                    )
                    
                    # Create lessons for each module
                    lesson_types = ['video', 'text', 'quiz']
                    for j in range(3):  # 3 lessons per module
                        lesson_type = random.choice(lesson_types)
                        Lesson.objects.create(
                            module=module,
                            title=f"Lesson {j+1}: {module_data['title']} Part {j+1}",
                            description=f"Detailed explanation of {module_data['title'].lower()}",
                            lesson_type=lesson_type,
                            content=f"This is the content for lesson {j+1} of {module_data['title']}",
                            duration_minutes=random.randint(10, 45),
                            order=j+1,
                            is_published=True,
                            is_free_preview=(j == 0)  # First lesson is free preview
                        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample courses data!')
        )