from django.urls import path, include
from api.views import get_client, get_tariffs, get_detailed_tariff, create_client
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('clients/<int:chat_id>', get_client),
    path('all_tariffs/', get_tariffs),
    path('clients/add/', create_client),
    path('tariff/<str:tariff_name>', get_detailed_tariff),
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
