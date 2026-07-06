from django.db import models
from django.conf import settings
# from django.contrib.auth.models import User

class Recipe(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_recipes')
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    servings = models.PositiveIntegerField(default=4)
    ingredients = models.JSONField()  # List of ingredient names
    time_minutes = models.IntegerField()
    cooking_technologies = models.JSONField(default=list)
    dietary_tags = models.JSONField(default=list, blank=True)
    picture = models.ImageField(upload_to='static/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Vector embedding for similarity search
    embedding = models.JSONField(default=list, blank=True)

class RecipeLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')


class RecipeComment(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class RecipeMade(models.Model):
    """An 'I made this' post from someone other than the recipe's creator —
    distinct from Recipe.picture, which is the creator's own photo."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='static/', blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class RecipeCollection(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    recipes = models.ManyToManyField(Recipe, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)