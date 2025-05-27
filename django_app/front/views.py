from django.shortcuts import render,redirect
from django.views.generic import TemplateView
from django.urls import reverse_lazy


# Vues personnalisées pour les erreurs 404, 405 et 500
class CustomError404View(TemplateView):
    template_name = '404.html'
    status_code = 404

class CustomError405View(TemplateView):
    template_name = '405.html'
    status_code = 405

class CustomError500View(TemplateView):
    template_name = '500.html'
    status_code = 500
    
    
class WelcomeView(TemplateView):
    template_name = 'welcome.html'

class AboutView(TemplateView):
    template_name = 'about.html'

class ContactView(TemplateView):
    template_name = 'contact.html'
class DocumentationView(TemplateView):
    template_name = 'documentation.html'

class ServicesView(TemplateView):
    template_name = 'services.html'
    
class SolutionView(TemplateView):
    template_name = 'solution.html'

class LegalNoticeView(TemplateView):
    template_name = 'mentions_legales.html'

class ChangelogView(TemplateView):
    template_name = 'changelog.html'
    
class CustomLoginView(TemplateView):
    template_name = "login.html"
class CustomRegistrationView(TemplateView):
    template_name = "registration.html"

class ForgotPasswordView(TemplateView):
    template_name = "forgot_password.html"

class DemoTranslateView(TemplateView):
    template_name = "translate.html"
    
class ConfirmationView(TemplateView):
    template_name = 'confirmation.html'

    def get(self, request):
        if request.session.get('inscription_reussie', False):
            # Marqueur présent dans la session, affichez la page de confirmation
            request.session.clear()  # Videz la session après avoir affiché la page de confirmation
            return render(request, self.template_name)
        else:
            # Marqueur non présent dans la session, redirigez vers une autre page
            return redirect('front:welcome')  # Redirigez vers la page d'accueil


class SuccessView(TemplateView):
    template_name = "success.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse_lazy('front:welcome'))  # Rediriger vers la page d'accueil si personne n'est connecté
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter ici la logique pour récupérer le nom de l'utilisateur connecté
        user = self.request.user
        if user.is_authenticated:
            context['username'] = user.username  # Exemple : Récupérer le nom d'utilisateur
        return context


# NOUVELLE VIEW POUR CHAQUE SERVICES 

class ErpServices(TemplateView):
    template_name = 'ERP.html'        
    
class WebDevelopment(TemplateView):
    template_name = 'developpement_web.html'

class MobileDevelopment(TemplateView):
    template_name = 'developpement_mobile.html'

class DesignService(TemplateView):
    template_name = 'design.html'

class DigitalCommunication(TemplateView):
    template_name = 'communication_digitale.html'

class CustomSolutions(TemplateView):
    template_name = 'solutions_sur_mesure.html'

class PrintingService(TemplateView):
    template_name = 'impression_serigraphie.html'    
    
    
    