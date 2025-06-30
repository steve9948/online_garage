from django.db import models

# Create your models here.

from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models

class Profile(models.Model):
    class UserType(models.TextChoices):
        CAR_OWNER = 'OWNER', 'Car Owner'
        GARAGE_ADMIN = 'ADMIN', 'Garage Admin'
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=5, choices=UserType.choices, default=UserType.CAR_OWNER)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    def __str__(self): return f"{self.user.username}'s Profile"

class Garage(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='garages')
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    location = gis_models.PointField(srid=4326)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self): return self.name

class GarageService(models.Model):
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='services_offered')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta: unique_together = ('garage', 'service')
    def __str__(self): return f"{self.garage.name} - {self.service.name}"

class PartCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    class Meta: verbose_name_plural = "Part Categories"
    def __str__(self): return self.name

class Part(models.Model):
    seller_garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='parts_for_sale')
    category = models.ForeignKey(PartCategory, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='parts/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    def __str__(self): return self.name

class Review(models.Model):
    garage = models.ForeignKey(Garage, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('garage', 'user')
    def __str__(self): return f"Review for {self.garage.name} by {self.user.username}"

class ForumThread(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Post by {self.author.username} in '{self.thread.title}'"
