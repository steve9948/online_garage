from django.shortcuts import render

# Create your views here.
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, generics, permissions
from django.shortcuts import get_object_or_404
from .models import Garage, Part, Review, ForumThread, ForumPost
from .serializers import (
    GarageSerializer, PartSerializer, ReviewSerializer,
    ForumThreadSerializer, ForumPostSerializer
)
from .permissions import IsOwnerOrReadOnly

class GarageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GarageSerializer
    queryset = Garage.objects.filter(is_verified=True).prefetch_related('reviews', 'services_offered__service')

    def get_queryset(self):
        queryset = super().get_queryset()
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        if lat and lon:
            try:
                user_location = Point(float(lon), float(lat), srid=4326)
                queryset = queryset.annotate(distance=Distance('location', user_location)).order_by('distance')
            except (ValueError, TypeError): pass
        city = self.request.query_params.get('city')
        if city: queryset = queryset.filter(city__iexact=city)
        return queryset

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
