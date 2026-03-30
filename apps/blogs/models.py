from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from apps.core.models import BaseModel
from apps.courses.models import Category, Tag

User = get_user_model()


class Blog(BaseModel):
    """Blog post model"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='blogs')
    tags = models.ManyToManyField('courses.Tag', blank=True, related_name='blogs')
    
    image_src = models.CharField(max_length=500, blank=True, null=True, help_text="URL or path to blog image")
    description = models.TextField(help_text="Short description/summary")
    content = models.TextField(help_text="Full blog content (up to 2000 words)")
    
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Blogs"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Set published_at when first published
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title