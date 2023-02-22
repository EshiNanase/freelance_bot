from django.urls import path
from api.views import get_client, create_client
from api.views import get_freelancer, create_freelancer
from api.views import get_tariffs, get_detailed_tariff
from api.views import get_orders, get_detailed_order, create_order
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('all_tariffs/', get_tariffs),
    path('tariff/<str:tariff_name>', get_detailed_tariff),
    path('clients/add/', create_client),
    path('clients/<int:chat_id>', get_client),
    path('freelancers/add', create_freelancer),
    path('freelancers/<int:chat_id>', get_freelancer),
    path('all_orders/', get_orders),
    path('order/add', create_order),
    path('order/<int:order_id>', get_detailed_order),
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
