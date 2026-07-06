from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0002_recipe_dietary_tags_recipe_instructions_and_more"),
    ]

    operations = [
        TrigramExtension(),
    ]
