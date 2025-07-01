from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'garages', views.GarageViewSet, basename='garage')
router.register(r'parts', views.PartViewSet, basename='part')
router.register(r'forum/threads', views.ForumThreadViewSet, basename='forumthread')

urlpatterns = [
    path('', include(router.urls)),
    path('garages/<int:garage_pk>/reviews/', views.ReviewListCreateView.as_view(), name='garage-reviews'),
]