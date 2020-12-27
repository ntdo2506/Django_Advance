from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the public available ingredients API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test the authorized user ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'do@gmail.com', 'testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving ingredients"""
        Ingredient.objects.create(user=self.user, name='Do')
        Ingredient.objects.create(user=self.user, name='Vuong')
        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are for the authenticated user"""
        user2 = get_user_model().objects.create_user(
            'do1@gmail.com', 'testpass')
        Ingredient.objects.create(user=user2, name='Test')
        ingredient = Ingredient.objects.create(user=self.user, name='Do')
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new ingredient"""
        payload = {'name': 'Test tag'}
        self.client.post(INGREDIENTS_URL, payload)
        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating a new ingredient with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Test 1")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Test 2")
        recipe = Recipe.objects.create(
            title="Test title",
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe.tags.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredient_assigned_unique(self):
        """Test filtering ingredients by assigned returns unique items"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Test 1")
        Ingredient.objects.create(user=self.user, name="Test 2")
        recipe1 = Recipe.objects.create(
            title="Test title",
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe1.ingredient.add(ingredient1)
        recipe2 = Recipe.objects.create(
            title="Test title 2",
            time_minutes=10,
            price=5.00,
            user=self.user
        )
        recipe2.ingredient.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        self.assertIn(len(res.data), 1)
