from django.shortcuts import render

# Modify this file: api/views.py

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, generics, permissions
from django.shortcuts import get_object_or_404
from geopy.geocoders import Nominatim  # <-- Import the geocoder

from .models import Garage, Part, Review, ForumThread
from .serializers import (
    GarageSerializer, PartSerializer, ReviewSerializer, ForumThreadSerializer
)
from .permissions import IsOwnerOrReadOnly

# --- HEAVY MODIFICATION: Change GarageViewSet to a full ModelViewSet ---
class GarageViewSet(viewsets.ModelViewSet):
    serializer_class = GarageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    queryset = Garage.objects.all().prefetch_related('reviews', 'services_offered__service')

    def get_queryset(self):
        # We want to show all garages for potential editing by owners/staff,
        # but only verified ones for public viewers.
        queryset = super().get_queryset()
        if not self.request.user.is_staff and self.action == 'list':
            queryset = queryset.filter(is_verified=True)

        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                queryset = queryset.annotate(distance=Distance('location', user_location)).order_by('distance')
            except (ValueError, TypeError): pass
        
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__iexact=city)
        return queryset

    def perform_create(self, serializer):
        # Automatically set owner and geocode address to get coordinates
        address = serializer.validated_data.get('address', '')
        city = serializer.validated_data.get('city', '')
        point = self.geocode_address(f"{address}, {city}")
        serializer.save(owner=self.request.user, location=point)

    def perform_update(self, serializer):
        # Re-geocode address if it has changed
        address = serializer.validated_data.get('address')
        city = serializer.validated_data.get('city')
        point = serializer.instance.location # Keep old point by default
        if address or city: # If address or city is part of the update
            full_address = f"{address or serializer.instance.address}, {city or serializer.instance.city}"
            point = self.geocode_address(full_address)
        serializer.save(location=point)

    def geocode_address(self, address):
        geolocator = Nominatim(user_agent="online_garage_app")
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return Point(location.longitude, location.latitude, srid=4326)
        except Exception as e:
            print(f"Geocoding error: {e}")
        return Point(0, 0, srid=4326) # Return default point if geocoding fails


class PartViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Part.objects.filter(is_available=True).select_related('seller_garage', 'category')
    serializer_class = PartSerializer

class ForumThreadViewSet(viewsets.ModelViewSet):
    queryset = ForumThread.objects.all().prefetch_related('posts__author').select_related('author')
    serializer_class = ForumThreadSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    def perform_create(self, serializer): serializer.save(author=self.request.user)

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get_queryset(self):
        return Review.objects.filter(garage_id=self.kwargs['garage_pk']).select_related('user')
    def perform_create(self, serializer):
        garage = get_object_or_404(Garage, pk=self.kwargs['garage_pk'])
        serializer.save(user=self.request.user, garage=garage)