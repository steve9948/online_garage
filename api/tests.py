from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point # For GeoDjango Point objects
from rest_framework import status
from rest_framework.test import APIClient

# models you need to create or check in your tests
from .models import Garage, Service, GarageService

class AuthenticatedGarageAPITests(TestCase):

    def setUp(self):
        """Set up a user and an API client for authenticated tests."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testcreator',
            email='creator@test.com',
            password='strongpassword123'
        )
        # Authenticate the client for all tests in this class
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_user_cannot_create_garage(self):
        """
        Verify that a 401 Unauthorized is returned for unauthenticated users.
        """
        # Create a new unauthenticated client for this specific test
        unauthenticated_client = APIClient()
        url = reverse('garage-list')
        payload = {'name': 'Should Fail Garage'}
        response = unauthenticated_client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create_garage_with_services(self):
        """
        Verify an authenticated user can create a garage and its services.
        """
        url = reverse('garage-list')
        payload = {
            "name": "Testable Auto Works",
            "description": "A garage created during an automated test.",
            "address": "101 Test Parkway",
            "city": "Nairobi",
            "country": "Kenya",
            "phone_number": "+254123456789",
            "email": "contact@testable.auto",
            "services": [
                {"service": "Automated Oil Change", "price": "55.00"},
                {"service": "Robotic Tire Rotation", "price": "45.00"}
            ]
        }

        response = self.client.post(url, payload, format='json')

        # 1. Check if the request was successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 2. Check if the garage was actually created in the database
        self.assertEqual(Garage.objects.count(), 1)
        garage = Garage.objects.first()
        self.assertEqual(garage.name, "Testable Auto Works")
        self.assertEqual(garage.owner, self.user)

        # 3. Check if the new services were created
        self.assertTrue(Service.objects.filter(name="Automated Oil Change").exists())
        self.assertTrue(Service.objects.filter(name="Robotic Tire Rotation").exists())

        # 4. Check if the services were correctly linked to the garage
        self.assertEqual(garage.services_offered.count(), 2)

    def test_geocoding_on_garage_creation(self):
        """
        Verify that the geocoding feature populates the location field.
        Note: This test relies on an external service (Nominatim) and may be slow or fail
        if there's no internet connection. In a larger app, you would "mock" this.
        """
        url = reverse('garage-list')
        payload = {
            "name": "Geocoded Garage",
            "description": "A test garage that should be geocoded automatically.",
            "address": "Eiffel Tower", # Using a famous landmark for a reliable geocode
            "city": "Paris",
            "country": "France",
            "phone_number": "123",
            "email": "geo@test.com",
            "services": []
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        garage = Garage.objects.get(name="Geocoded Garage")
        
        # Check that the location is not the default (0, 0)
        self.assertNotEqual(garage.location, Point(0, 0, srid=4326))
        
        # Check if the coordinates are roughly correct for the Eiffel Tower (lon: 2.29, lat: 48.85)
        self.assertAlmostEqual(garage.location.x, 2.29, places=1) # lon
        self.assertAlmostEqual(garage.location.y, 48.85, places=1) # lat
    
    def test_cannot_create_garage_with_no_db_name(self):
        '''
        Verify that creating a garage without a requiresd field fails correctly.
        '''
        url = reverse('garage-list')
        payload = {
            # 'name' is intentionally missing
            "description": "This garage has no name.",
            "address": "123 Failure Lane",
            "city": "Errorville",
            "country": "Testland",
            "phone_number": "555-0101",
            "email": "noname@test.com",
        }
        response = self.client.post(url, payload, format='json')
        
        #Assert that the correct error code was returned
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        #Asset that the error message correctly identifies the "name" field as the problem
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'][0], 'This field is required.')
