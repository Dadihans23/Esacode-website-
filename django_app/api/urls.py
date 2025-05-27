from django.urls import path
from .views import detect_language, translate_text,create_page,create_and_translate_page

app_name = 'api'

urlpatterns = [
    path('detect/', detect_language, name='detect_language'),
    path('translate/', translate_text, name='translate_text'),
    path('create-page/', create_page, name='create_page'),
    path('create-translate-page/', create_and_translate_page, name='create_and_translate_page'),

]
