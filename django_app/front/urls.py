from django.urls import path
from .views import (
    WelcomeView, AboutView, DocumentationView, ContactView, 
    CustomLoginView, CustomRegistrationView, ConfirmationView, 
    SolutionView, ChangelogView, DemoTranslateView, 
    ForgotPasswordView, SuccessView, CustomError404View, 
    CustomError405View, CustomError500View, ServicesView,
    LegalNoticeView , # Ajout de la nouvelle vue , 
    ErpServices , WebDevelopment,
    MobileDevelopment,
    DesignService,
    DigitalCommunication,
    CustomSolutions,
    PrintingService,
)

app_name = 'front'

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('about/', AboutView.as_view(), name='about'),
    path('documentation/', DocumentationView.as_view(), name='documentation'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('solutions/', SolutionView.as_view(), name='solutions'),
    path('services/', ServicesView.as_view(), name='services'),
    path('journal/', ChangelogView.as_view(), name='journal des modifications'),
    path('demo_translate/', DemoTranslateView.as_view(), name='Translate'),
    path('register/', CustomRegistrationView.as_view(), name='register'),
    path('confirmation/', ConfirmationView.as_view(), name='confirmation'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('success/', SuccessView.as_view(), name='success'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('mentions-legales/', LegalNoticeView.as_view(), name='mentions_legales'),  # Nouvelle URL
    
    
    # NOUVELLE URL POUR LES DIFFERENTS SERVICES 
    path('erp-services/', ErpServices.as_view(), name='erp_services'),  
    path('developpement-web/', WebDevelopment.as_view(), name='web_development'),
    path('developpement-mobile/', MobileDevelopment.as_view(), name='mobile_development'),
    path('design/', DesignService.as_view(), name='design_service'),
    path('communication-digitale/', DigitalCommunication.as_view(), name='digital_communication'),
    path('solutions-sur-mesure/', CustomSolutions.as_view(), name='custom_solutions'),
    path('impression-serigraphie/', PrintingService.as_view(), name='printing_service'),

    
]

# Configuration des vues personnalisées pour les erreurs 404, 405 et 500
handler404 = CustomError404View.as_view()
handler405 = CustomError405View.as_view()

handler500 = CustomError500View.as_view()