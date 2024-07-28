from django.urls import path, include
from . import views
from .views import search_suggestions
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    #path('myapp/', include('myapp.urls')),
    path('search_results/', views.search_results, name='search_results'),
    path('search-suggestions/', search_suggestions, name='search-suggestions'),
    path('search_results_sorted/', views.search_results_sorted, name='search_results_sorted'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
