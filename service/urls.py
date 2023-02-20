from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import view_index, view_freelancer_orders

app_name = 'service'

urlpatterns = [
    path('', view_index, name='index'),
    path('freelancer_orders/', view_freelancer_orders, name='freelancer_orders')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
