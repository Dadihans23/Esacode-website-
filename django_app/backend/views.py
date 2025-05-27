from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages


def register_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Vérifier si les mots de passe correspondent
        if password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('front:register')  # Rediriger vers la page d'inscription avec le message d'erreur

        # Vérifier si l'email est déjà utilisé comme username
        if User.objects.filter(username=email).exists():
            messages.error(request, "Cet email est déjà utilisé comme identifiant.")
            return redirect('front:register')  # Rediriger vers la page d'inscription avec le message d'erreur

        # Créer un nouvel utilisateur avec l'email comme username
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        # Stockez un marqueur dans la session pour indiquer une inscription réussie
        request.session['inscription_reussie'] = True

        # Rediriger l'utilisateur vers la page de confirmation
        return redirect('front:confirmation')


    return redirect('front:register')

def login_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            # Rediriger vers la page de succès ou autre
            return redirect('front:success')  # Rediriger vers la page de succès après la connexion
        else:
            try:
                user = User.objects.get(email=email)
                messages.error(request, "Mot de passe incorrect.")
            except User.DoesNotExist:
                messages.error(request, "Adresse e-mail incorrecte.")

            return redirect('front:login')  # Rediriger vers la page de connexion avec le message d'erreur

    # Si la méthode est GET ou si l'authentification échoue, afficher à nouveau le formulaire de connexion
    return redirect('front:login')

def logout_user(request):
    logout(request)
    return redirect('front:welcome')  # Rediriger vers la page d'accueil après la déconnexion