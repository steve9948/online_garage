from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction, models
from .models import (
    Garage, Part, Review, ForumThread, ForumPost, Service, GarageService
)
from .fields import CreatableSlugRelatedField  # <-- Import our new field

# --- No changes to UserSerializer and ReviewSerializer ---
class UserSerializer(serializers.ModelSerializer):
    class Meta: model = User; fields = ['id', 'username', 'email']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta: model = Review; fields = ['id', 'user', 'rating', 'comment', 'created_at']; read_only_fields = ['user']

# --- NEW: A serializer for WRITING service data ---
class GarageServiceWriteSerializer(serializers.ModelSerializer):
    service = CreatableSlugRelatedField(
        queryset=Service.objects.all(),
        slug_field='name'  # We'll use the 'name' field to find or create the Service
    )
    class Meta: model = GarageService; fields = ['service', 'price']

# --- RENAME: The old serializer is now for READING data ---
class GarageServiceReadSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    class Meta: model = GarageService; fields = ['id', 'service_name', 'price']

# --- HEAVY MODIFICATION: Update the main GarageSerializer ---
class GarageSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    services_offered = GarageServiceReadSerializer(many=True, read_only=True)
    distance_km = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    # This new field is for INPUT ONLY (write_only=True)
    services = serializers.ListField(
        child=GarageServiceWriteSerializer(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Garage
        fields = [
            'id', 'name', 'description', 'address', 'city', 'country', 'phone_number',
            'email', 'website', 'location', 'owner', 'reviews', 'services_offered',
            'services', 'distance_km', 'average_rating'
        ]
        read_only_fields = ['owner', 'location']  # Location will be set automatically

    def get_distance_km(self, obj):
        if hasattr(obj, 'distance'): return round(obj.distance.m / 1000, 2)
        return None

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(models.Avg('rating')).get('rating__avg')
        return round(avg, 1) if avg else None

    # Implement create and update to handle the nested 'services' data
    @transaction.atomic
    def create(self, validated_data):
        services_data = validated_data.pop('services', [])
        garage = Garage.objects.create(**validated_data)
        for service_data in services_data:
            GarageService.objects.create(garage=garage, **service_data)
        return garage

    @transaction.atomic
    def update(self, instance, validated_data):
        services_data = validated_data.pop('services', None)
        instance = super().update(instance, validated_data)
        if services_data is not None:
            instance.services_offered.all().delete()
            for service_data in services_data:
                GarageService.objects.create(garage=instance, **service_data)
        return instance

# --- No changes to PartSerializer, ForumPostSerializer, ForumThreadSerializer ---
class PartSerializer(serializers.ModelSerializer):
    seller_garage = serializers.StringRelatedField(); category = serializers.StringRelatedField()
    class Meta: model = Part; fields = '__all__'
class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta: model = ForumPost; fields = ['id', 'author', 'content', 'created_at']
class ForumThreadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True); posts = ForumPostSerializer(many=True, read_only=True)
    class Meta: model = ForumThread; fields = ['id', 'title', 'author', 'created_at', 'posts']