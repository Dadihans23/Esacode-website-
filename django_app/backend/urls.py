from django.urls import path
from .views import register_user,login_user,logout_user

app_name = 'backend'  # Définissez le namespace pour votre application backend

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),  # Ajoutez la route pour la connexion
    path('logout/', logout_user, name='logout_user'),  # Ajoutez la route de déconnexion


    # Autres URLs de votre application backend
]
