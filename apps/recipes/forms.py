from django import forms
from .models import Recipe, RecipeComment, RecipeMade, RecipeCollection
from .constants import INGREDIENT_CHOICES, COOKING_TECHNOLOGY_CHOICES, DIETARY_TAG_CHOICES

INGREDIENT_FORM_CHOICES = [(i, i) for i in INGREDIENT_CHOICES]
COOKING_TECH_FORM_CHOICES = [(t, t) for t in COOKING_TECHNOLOGY_CHOICES]
DIETARY_TAG_FORM_CHOICES = [(t, t) for t in DIETARY_TAG_CHOICES]


class RecipeForm(forms.ModelForm):
    ingredients = forms.MultipleChoiceField(
        choices=INGREDIENT_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    cooking_technologies = forms.MultipleChoiceField(
        choices=COOKING_TECH_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    dietary_tags = forms.MultipleChoiceField(
        choices=DIETARY_TAG_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Recipe
        fields = [
            'title', 'instructions', 'servings', 'ingredients', 'time_minutes',
            'cooking_technologies', 'dietary_tags', 'picture',
        ]
        widgets = {
            'instructions': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Steps, one per line'}),
            'servings': forms.NumberInput(attrs={'min': 1}),
            'time_minutes': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Minutes'}),
        }


class RecipeSearchForm(forms.Form):
    MATCH_MODE_CHOICES = [('any', 'Any of these'), ('all', 'All of these')]
    SORT_CHOICES = [
        ('relevance', 'Most liked'),
        ('newest', 'Newest'),
        ('quickest', 'Quickest'),
        ('closest_match', 'Closest match to my ingredients'),
    ]

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search by recipe title...'}),
        label='Title',
    )
    ingredients = forms.MultipleChoiceField(
        choices=INGREDIENT_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Ingredients on hand',
    )
    match_mode = forms.ChoiceField(
        choices=MATCH_MODE_CHOICES,
        required=False,
        initial='any',
        label='Match',
    )
    max_time = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Max time (minutes)'}),
        label='Maximum cooking time'
    )
    cooking_technologies = forms.MultipleChoiceField(
        choices=COOKING_TECH_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Available cooking tech'
    )
    dietary_tags = forms.MultipleChoiceField(
        choices=DIETARY_TAG_FORM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Dietary needs',
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='relevance',
        label='Sort by',
    )


class RecipeCommentForm(forms.ModelForm):
    class Meta:
        model = RecipeComment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...'}),
        }


class RecipeMadeForm(forms.ModelForm):
    class Meta:
        model = RecipeMade
        fields = ['photo', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2, 'placeholder': 'How did it go?'}),
        }


class RecipeCollectionForm(forms.ModelForm):
    class Meta:
        model = RecipeCollection
        fields = ['name']
