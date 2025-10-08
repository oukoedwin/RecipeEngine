from pathlib import Path

MAX_COOK_TIME = 240.0  # Maximum cooking time in minutes

ROOT_URLCONF = 'recipe_project.urls'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# DATABASES = { # TODO:requires installation of postgres
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'recipe_db',
#         'USER': 'user',
#         'PASSWORD': 'password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# For vector operations, consider adding:
# pip install django-extensions psycopg2-binary