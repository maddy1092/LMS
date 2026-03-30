from django.contrib import admin
from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_published', 'created_at']
    list_filter = ['is_published', 'category', 'created_at']
    search_fields = ['title', 'description', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['slug', 'published_at']
    fields = [
        'title', 'slug', 'author', 'category', 'tags',
        'image_src', 'description', 'content',
        'is_published', 'published_at', 'created_at', 'updated_at'
    ]