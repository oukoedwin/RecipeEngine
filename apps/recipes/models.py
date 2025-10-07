

class Recipe(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_recipes')
    ingredients = models.JSONField()  # List of ingredient names
    time_minutes = models.IntegerField()
    cooking_technologies = models.JSONField(default=list)
    picture = models.ImageField(upload_to='recipes/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Vector embedding for similarity search
    embedding = models.JSONField(default=list, blank=True)
    
class RecipeLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'recipe')