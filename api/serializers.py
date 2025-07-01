from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Garage, Part, Review, ForumThread, ForumPost, Service, GarageService
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['user']

class GarageServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    class Meta:
        model = GarageService
        fields = ['id', 'service_name', 'price']

class GarageSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    services_offered = GarageServiceSerializer(many=True, read_only=True)
    distance_km = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Garage
        fields = [
            'id', 'name', 'description', 'address', 'city', 'phone_number',
            'email', 'website', 'location', 'owner', 'reviews', 'services_offered',
            'distance_km', 'average_rating'
        ]
    
    def get_distance_km(self, obj):
        if hasattr(obj, 'distance'):
            return round(obj.distance.m / 1000, 2)
        return None
    
    def get_average_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(Avg('rating')).get('rating__avg')
        return round(avg, 1) if avg else None

class PartSerializer(serializers.ModelSerializer):
    seller_garage = serializers.StringRelatedField()
    category = serializers.StringRelatedField()
    class Meta:
        model = Part
        fields = '__all__'

class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta:
        model = ForumPost
        fields = ['id', 'author', 'content', 'created_at']

class ForumThreadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    posts = ForumPostSerializer(many=True, read_only=True)
    class Meta:
        model = ForumThread
        fields = ['id', 'title', 'author', 'created_at', 'posts']