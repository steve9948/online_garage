from rest_framework import serializers
from .models import Service

class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Custom field to allow creation of related objects using slugs.
    """
    def to_internal_value(self, data):
        try:
            # try to get the object by its unique slug
            return self.get_queryset().get(**{self.slug_field: data})
        except Service.DoesNotExist:
            # if it doesn't exist, create a new object
            return self.get_queryset().create(**{self.slug_field: data})
        except(TypeError, ValueError):
            self.fail('invalid')