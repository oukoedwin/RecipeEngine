from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),
    path('auth/token/', obtain_auth_token, name='api-token-auth'),
    path('accounts/', include('apps.accounts.api_urls')),
    path('recipes/', include('apps.recipes.api_urls')),
    path('social/', include('apps.social.api_urls')),
]
