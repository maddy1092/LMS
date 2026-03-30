from rest_framework import serializers
from django.utils import timezone
from apps.courses.models import Category, Tag
from apps.courses.serializers import CategorySerializer
from .models import Blog


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class BlogListSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'image_src', 'description',
            'category', 'category_name', 'tags', 'tag_ids',
            'author_name', 'created_at', 'published_at', 'is_published'
        ]
    
    def get_author_name(self, obj):
        try:
            profile = obj.author.userprofile
            full_name = f"{profile.first_name} {profile.last_name}".strip()
            if full_name:
                return full_name
        except:
            pass
        return obj.author.email
    
    def get_category_name(self, obj):
        return obj.category.title if obj.category else None


class BlogDetailSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'slug', 'image_src', 'description', 'content',
            'category', 'tags', 'tag_ids', 'author', 'created_at', 
            'updated_at', 'published_at', 'is_published'
        ]
    
    def get_author(self, obj):
        try:
            profile = obj.author.userprofile
            return {
                'id': obj.author.id,
                'email': obj.author.email,
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'avatar': profile.avatar
            }
        except:
            return {
                'id': obj.author.id,
                'email': obj.author.email,
                'first_name': '',
                'last_name': '',
                'avatar': ''
            }


class BlogCreateUpdateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Blog
        fields = [
            'title', 'image_src', 'description', 'content',
            'category', 'tag_ids', 'is_published'
        ]
    
    def validate_content(self, value):
        # Rough word count check (split by whitespace)
        word_count = len(value.split())
        if word_count > 2000:
            raise serializers.ValidationError("Content exceeds 2000 words limit")
        return value
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        request = self.context.get('request')
        validated_data['author'] = request.user
        blog = super().create(validated_data)
        blog.tags.set(tag_ids)
        return blog
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        blog = super().update(instance, validated_data)
        if tag_ids is not None:
            blog.tags.set(tag_ids)
        return blog