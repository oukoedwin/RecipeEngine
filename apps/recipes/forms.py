from django import forms
from .models import Recipe

class RecipeForm(forms.ModelForm):
    ingredients = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter ingredients, one per line'}),
        help_text='List ingredients separated by commas or new lines'
    )
    cooking_technologies = forms.MultipleChoiceField(
        choices=[('Oven', 'Oven'), ('Grill', 'Grill'), ('Microwave', 'Microwave')],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Recipe
        fields = ['ingredients', 'time_minutes', 'cooking_technologies', 'picture']
        widgets = {
            'time_minutes': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Minutes'}),
        }
    
    def clean_ingredients(self):
        # Convert text input to list
        ingredients = self.cleaned_data['ingredients']
        return [ing.strip() for ing in ingredients.replace('\n', ',').split(',') if ing.strip()]


class RecipeSearchForm(forms.Form):
    ingredients = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search ingredients...'}),
        help_text='Comma-separated ingredients'
    )
    max_time = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Max time (minutes)'}),
        label='Maximum cooking time'
    )
    cooking_technologies = forms.MultipleChoiceField(
        choices=[('Oven', 'Oven'), ('Grill', 'Grill'), ('Microwave', 'Microwave')],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Available cooking tech'
    )
    
    def clean_ingredients(self):
        ingredients = self.cleaned_data.get('ingredients', '')
        if ingredients:
            return [ing.strip() for ing in ingredients.split(',') if ing.strip()]
        return None