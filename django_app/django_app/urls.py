from django.contrib import admin
from django.urls import path, include
# from django.conf.urls.static import static
# from django.conf import settings

urlpatterns = [
    path('welcomesuperadmin/', admin.site.urls),
    path('', include('front.urls')), # Ajoutez cette ligne pour inclure les URL de l'application "front"
    path('api/', include('api.urls')), # Ajoutez cette ligne pour inclure les URL de l'application "api"
    path('backend/', include('backend.urls')), # Inclure les URL de l'application "backend"

    # Ajoutez d'autres URL au besoin
    # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
]
