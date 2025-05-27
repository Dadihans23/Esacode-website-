"""
Service de traduction complet avec support multilingue et gestion spécialisée des langues africaines.
Auteur: ESA Code
Version: 2.0.2
Date: 2024-02-20

API Endpoints:
- POST /api/detect/: Détection de langue
- POST /api/translate/: Traduction de texte
- POST /api/create-page/: Création de page
- POST /api/create-translate-page/: Création et traduction

Features:
- Support multilingue
- Gestion spéciale des langues africaines
- Cache système
- Logging sécurisé
- Gestion d'erreurs améliorée
- Validation des entrées
"""

import json
import logging
import requests
import langid
from time import time
from datetime import datetime
from typing import Dict, Tuple, Optional, Union
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ADMIN_TOKEN = getattr(settings, 'ADMIN_TOKEN', 'votre_token_secret')
CACHE_TIMEOUT = 3600  # 1 hour
MAX_TEXT_LENGTH = 5000
DEFAULT_SOURCE_LANG = 'auto'
TRANSLATION_TIMEOUT = 30
THREAD_POOL_MAX_WORKERS = 1
CACHE_KEY_PREFIX = "trans_"
DETECT_CACHE_KEY_PREFIX = "lang_detect_"

# Messages d'erreur utilisateur
USER_FRIENDLY_MESSAGES = {
    'RequestException': 'Service temporairement indisponible. Veuillez réessayer plus tard.',
    'JSONDecodeError': 'Format de données invalide.',
    'ValueError': 'Les données fournies sont incorrectes.',
    'TimeoutError': 'Le service met trop de temps à répondre. Veuillez réessayer.',
    'TranslationError': 'La traduction a échoué. Veuillez réessayer.',
    'ConnectionError': 'Impossible de se connecter au service. Veuillez réessayer plus tard.',
    'Exception': 'Une erreur inattendue est survenue. Veuillez réessayer plus tard.'
}

# Dictionnaire des langues africaines
AFRICAN_LANGUAGES = {
    "fon": "Fon (Bénin)",
    "wo": "Wolof (Sénégal)",
    "aa": "Afar (Éthiopie)",
    "bci": "Baoulé (Côte d'Ivoire)",
    "bem": "Bemba (Zambie)",
    "luo": "Luo (Tanzanie)",
    "bm-Nkoo": "N'Ko (Mali)",
    "so": "Somali (Somalie)",
    "sus": "Soussou (Sierra Leone)",
    "ss": "Swati (Eswatini)",
    "run": "Kirundi (Burundi)",
    "tiv": "Tiv (Nigeria)",
    "tum": "Tumbuka (Malawi)",
    "gaa": "Ga (Ghana)",
    "ach": "Acholi (Ouganda, Soudan du Sud)",
    "alz": "Alur (Ouganda, République démocratique du Congo)",
    "am": "Amharique (Éthiopie)",
    "bm": "Bambara (Mali)",
    "ny": "Chichewa (Malawi, Zambie, Mozambique)",
    "dyu": "Dioula (Côte d’Ivoire, Burkina Faso, Mali)",
    "ee": "Ewe (Togo, Ghana)",
    "kr": "Kanuri (Nigeria, Niger, Tchad, Cameroun)",
    "kg": "Kikongo (République démocratique du Congo, Congo-Brazzaville, Angola)",
    "rw": "Kinyarwanda (Rwanda)",
    "ktu": "Kituba (République démocratique du Congo, Congo-Brazzaville)",
    "kri": "Krio (Sierra Leone)",
    "ln": "Lingala (République démocratique du Congo, Congo-Brazzaville)",
    "lg": "Luganda (Ouganda)",
    "nus": "Nuer (Soudan du Sud, Éthiopie)",
    "om": "Oromo (Éthiopie, Kenya)",
    "ff": "Peul (Afrique de l’Ouest et du Centre)",
    "sg": "Sango (République centrafricaine)",
    "st": "Sesotho (Lesotho, Afrique du Sud)",
    "sn": "Shona (Zimbabwe)",
    "sw": "Swahili (Kenya, Tanzanie, Ouganda, etc.)",
    "ber-Latn": "Tamazight (Berbère, Afrique du Nord, alphabet latin)",
    "ber": "Tamazight (Berbère, Afrique du Nord, Tifinagh)",
    "ti": "Tigrigna (Érythrée, Éthiopie)",
    "ts": "Tsonga (Mozambique, Afrique du Sud)",
    "tn": "Tswana (Botswana, Afrique du Sud)",
    "ve": "Venda (Afrique du Sud, Zimbabwe)",
    "xh": "Xhosa (Afrique du Sud)",
    "zu": "Zoulou (Afrique du Sud)"
}


LANGUAGE_CODES = {
    # Codes généraux
    'auto': 'auto',  # Détection automatique
    
    # Variations de chinois
    'zh': 'zh-CN',  # Chinois simplifié par défaut
    'zh-hans': 'zh-CN',  # Chinois simplifié explicite
    'zh-hant': 'zh-TW',  # Chinois traditionnel
    'zh-cn': 'zh-CN',
    'zh-tw': 'zh-TW',
    'zh-hk': 'zh-TW',  # Hong Kong utilise le traditionnel
    'chi': 'zh-CN',    # Code ISO ancien
    
    # Codes alternatifs courants
    'iw': 'he',     # Hébreu (ancien code -> nouveau)
    'jw': 'jv',     # Javanais
    'nb': 'no',     # Norvégien Bokmål -> Norvégien
    'nn': 'no',     # Norvégien Nynorsk -> Norvégien
    'baq': 'eu',    # Basque
    'chi': 'zh',    # Chinois
    'cze': 'cs',    # Tchèque
    'dut': 'nl',    # Néerlandais
    'ger': 'de',    # Allemand
    'gre': 'el',    # Grec
    'arm': 'hy',    # Arménien
    'ice': 'is',    # Islandais
    'per': 'fa',    # Persan
    'rum': 'ro',    # Roumain
    
    # Variantes régionales
    'en-us': 'en',  # Anglais US
    'en-gb': 'en',  # Anglais GB
    'fr-ca': 'fr',  # Français canadien
    'fr-fr': 'fr',  # Français de France
    'pt-br': 'pt',  # Portugais brésilien
    'pt-pt': 'pt',  # Portugais européen
    'es-es': 'es',  # Espagnol d'Espagne
    'es-mx': 'es',  # Espagnol du Mexique
    
    # Corrections courantes
    'fil': 'tl',    # Filipino -> Tagalog
    'he': 'iw',     # Hébreu (nouveau code -> ancien pour compatibilité)
    'ji': 'yi',     # Yiddish
    'in': 'id',     # Indonésien
    'gav': 'sw',    # Swahili
    
    # Variantes dialectales
    'cmn': 'zh',    # Mandarin
    'yue': 'zh',    # Cantonais
    'wuu': 'zh',    # Wu
    'hsn': 'zh',    # Xiang
    'hak': 'zh',    # Hakka
    'nan': 'zh',    # Min Nan
    
    # Codes ISO alternatifs
    'ara': 'ar',    # Arabe
    'ben': 'bn',    # Bengali
    'bul': 'bg',    # Bulgare
    'cat': 'ca',    # Catalan
    'dan': 'da',    # Danois
    'est': 'et',    # Estonien
    'fin': 'fi',    # Finnois
    'fra': 'fr',    # Français
    'geo': 'ka',    # Géorgien
    'hun': 'hu',    # Hongrois
    'ind': 'id',    # Indonésien
    'ita': 'it',    # Italien
    'jpn': 'ja',    # Japonais
    'kor': 'ko',    # Coréen
    'lat': 'la',    # Latin
    'lav': 'lv',    # Letton
    'lit': 'lt',    # Lituanien
    'mac': 'mk',    # Macédonien
    'may': 'ms',    # Malais
    'mlt': 'mt',    # Maltais
    'nor': 'no',    # Norvégien
    'pol': 'pl',    # Polonais
    'por': 'pt',    # Portugais
    'rus': 'ru',    # Russe
    'slo': 'sk',    # Slovaque
    'slv': 'sl',    # Slovène
    'spa': 'es',    # Espagnol
    'swe': 'sv',    # Suédois
    'tha': 'th',    # Thaï
    'tur': 'tr',    # Turc
    'ukr': 'uk',    # Ukrainien
    'vie': 'vi',    # Vietnamien
    
    # Langues moins courantes mais supportées
    'ace': 'id',    # Achinese -> Indonesian
    'ami': 'zh',    # Amis -> Chinese
    'ban': 'id',    # Balinese -> Indonesian
    'bug': 'id',    # Buginese -> Indonesian
    'min': 'id',    # Minangkabau -> Indonesian
    'bjn': 'id',    # Banjar -> Indonesian
    'mad': 'id',    # Madurese -> Indonesian
    'niu': 'en',    # Niuean -> English
    'tpi': 'en',    # Tok Pisin -> English
    
    # Codes obsolètes mais parfois encore utilisés
    'ins': 'id',    # Indonesian (old)
    'gax': 'om',    # Oromo
    'gaz': 'om',    # Oromo (alternative)
    'mol': 'ro',    # Moldavian -> Romanian
    'scr': 'hr',    # Croatian (old)
    
    # Variantes orthographiques
    'sr-latn': 'sr', # Serbe latin
    'sr-cyrl': 'sr', # Serbe cyrillique
    'uz-latn': 'uz', # Ouzbek latin
    'uz-cyrl': 'uz', # Ouzbek cyrillique
    'kmr': 'ku',     # Kurde du Nord
    'ckb': 'ku'  ,    # Kurde central
        **{code: code for code in AFRICAN_LANGUAGES.keys()}

}

# Dictionnaire complet des noms de langues

LANGUAGE_NAMES = {
    "auto": "Auto-detect",
    "af": "Afrikaans",
    "sq": "Albanian (Shqip)",
    "am": "Amharic (አማርኛ)",
    "ar": "Arabic (العربية)",
    "hy": "Armenian (Հայերեն)",
    "as": "Assamese (অসমীয়া)",
    "ay": "Aymara (Aymar)",
    "az": "Azerbaijani (Azərbaycan)",
    "bm": "Bambara (Bamanankan)",
    "eu": "Basque (Euskara)",
    "be": "Belarusian (Беларуская)",
    "bn": "Bengali (বাংলা)",
    "bho": "Bhojpuri (भोजपुरी)",
    "bs": "Bosnian (Bosanski)",
    "bg": "Bulgarian (Български)",
    "ca": "Catalan (Català)",
    "ceb": "Cebuano",
    "ny": "Chichewa",
    "zh": "Chinese (中文)",
    "zh-CN": "Chinese Simplified (简体中文)",
    "zh-TW": "Chinese Traditional (繁體中文)",
    "co": "Corsican (Corsu)",
    "hr": "Croatian (Hrvatski)",
    "cs": "Czech (Čeština)",
    "da": "Danish (Dansk)",
    "dv": "Dhivehi (ދިވެހި)",
    "doi": "Dogri (डोगरी)",
    "nl": "Dutch (Nederlands)",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian (Eesti)",
    "ee": "Ewe (Eʋegbe)",
    "fil": "Filipino (Tagalog)",
    "fi": "Finnish (Suomi)",
    "fr": "French (Français)",
    "fy": "Frisian (Frysk)",
    "gl": "Galician (Galego)",
    "ka": "Georgian (ქართული)",
    "de": "German (Deutsch)",
    "el": "Greek (Ελληνικά)",
    "gn": "Guarani (Avañe'ẽ)",
    "gu": "Gujarati (ગુજરાતી)",
    "ht": "Haitian Creole (Kreyòl ayisyen)",
    "ha": "Hausa (Hausa)",
    "haw": "Hawaiian (ʻŌlelo Hawaiʻi)",
    "he": "Hebrew (עברית)",
    "iw": "Hebrew (עברית)",
    "hi": "Hindi (हिन्दी)",
    "hmn": "Hmong (Hmoob)",
    "hu": "Hungarian (Magyar)",
    "is": "Icelandic (Íslenska)",
    "ig": "Igbo",
    "ilo": "Ilocano",
    "id": "Indonesian (Bahasa Indonesia)",
    "ga": "Irish (Gaeilge)",
    "it": "Italian (Italiano)",
    "ja": "Japanese (日本語)",
    "jv": "Javanese (Basa Jawa)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "kk": "Kazakh (Қазақ)",
    "km": "Khmer (ខ្មែរ)",
    "rw": "Kinyarwanda",
    "gom": "Konkani (कोंकणी)",
    "ko": "Korean (한국어)",
    "kri": "Krio",
    "ku": "Kurdish (Kurdî)",
    "ckb": "Kurdish Sorani (سۆرانی)",
    "ky": "Kyrgyz (Кыргызча)",
    "lo": "Lao (ລາວ)",
    "la": "Latin (Latina)",
    "lv": "Latvian (Latviešu)",
    "ln": "Lingala (Lingála)",
    "lt": "Lithuanian (Lietuvių)",
    "lg": "Luganda",
    "lb": "Luxembourgish (Lëtzebuergesch)",
    "mk": "Macedonian (Македонски)",
    "mai": "Maithili (मैथिली)",
    "mg": "Malagasy",
    "ms": "Malay (Bahasa Melayu)",
    "ml": "Malayalam (മലയാളം)",
    "mt": "Maltese (Malti)",
    "mi": "Maori (Te Reo Māori)",
    "mr": "Marathi (मराठी)",
    "mni-Mtei": "Meiteilon (Manipuri)",
    "lus": "Mizo",
    "mn": "Mongolian (Монгол)",
    "my": "Myanmar (Burmese) (မြန်မာ)",
    "ne": "Nepali (नेपाली)",
    "no": "Norwegian (Norsk)",
    "or": "Odia (Oriya) (ଓଡ଼ିଆ)",
    "om": "Oromo (Afaan Oromoo)",
    "ps": "Pashto (پښتو)",
    "fa": "Persian (فارسی)",
    "pl": "Polish (Polski)",
    "pt": "Portuguese (Português)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "qu": "Quechua (Runa Simi)",
    "ro": "Romanian (Română)",
    "ru": "Russian (Русский)",
    "sm": "Samoan (Gagana Samoa)",
    "sa": "Sanskrit (संस्कृत)",
    "gd": "Scots Gaelic (Gàidhlig)",
    "nso": "Sepedi",
    "sr": "Serbian (Српски)",
    "st": "Sesotho",
    "sn": "Shona (ChiShona)",
    "sd": "Sindhi (سنڌي)",
    "si": "Sinhala (සිංහල)",
    "sk": "Slovak (Slovenčina)",
    "sl": "Slovenian (Slovenščina)",
    "so": "Somali (Soomaali)",
    "es": "Spanish (Español)",
    "su": "Sundanese (Basa Sunda)",
    "sw": "Swahili (Kiswahili)",
    "sv": "Swedish (Svenska)",
    "tg": "Tajik (Тоҷикӣ)",
    "ta": "Tamil (தமிழ்)",
    "tt": "Tatar (Татар)",
    "te": "Telugu (తెలుగు)",
    "th": "Thai (ไทย)",
    "ti": "Tigrinya (ትግርኛ)",
    "ts": "Tsonga",
    "tr": "Turkish (Türkçe)",
    "tk": "Turkmen (Türkmen)",
    "ak": "Twi (Akan)",
    "uk": "Ukrainian (Українська)",
    "ur": "Urdu (اردو)",
    "ug": "Uyghur (ئۇيغۇرچە)",
    "uz": "Uzbek (O'zbek)",
    "vi": "Vietnamese (Tiếng Việt)",
    "cy": "Welsh (Cymraeg)",
    "xh": "Xhosa (isiXhosa)",
    "yi": "Yiddish (ייִדיש)",
    "yo": "Yoruba (Èdè Yorùbá)",
    "zu": "Zulu (isiZulu)",
    
    # Variantes régionales
    "pt-BR": "Brazilian Portuguese (Português do Brasil)",
    "pt-PT": "European Portuguese (Português de Portugal)",
    "es-ES": "Spanish (Spain)",
    "es-MX": "Spanish (Mexico)",
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "fr-CA": "French (Canada)",
    "fr-FR": "French (France)",
    
    # Autres variantes
    "sr-Latn": "Serbian (Latin)",
    "sr-Cyrl": "Serbian (Cyrillic)",
    "zh-Hans": "Chinese Simplified",
    "zh-Hant": "Chinese Traditional",
    "uz-Latn": "Uzbek (Latin)",
    "uz-Cyrl": "Uzbek (Cyrillic)",   
    
    # Fallback
    "unknown": "Unknown Language",
        **AFRICAN_LANGUAGES

    
}


def get_error_response(error: Exception, request) -> Tuple[dict, int]:
    """
    Génère une réponse d'erreur appropriée selon le type d'utilisateur.
    """
    error_type = type(error).__name__
    is_admin = (
        request.headers.get('X-Admin-Token') == ADMIN_TOKEN and
        request.headers.get('X-Debug-Mode') == 'true'
    )
    
    if is_admin:
        error_response = {
            'status': 'error',
            'message': str(error),
            'error_type': error_type,
            'details': {
                'traceback': str(error.__traceback__),
                'timestamp': datetime.now().isoformat()
            }
        }
    else:
        error_response = {
            'status': 'error',
            'message': USER_FRIENDLY_MESSAGES.get(error_type, USER_FRIENDLY_MESSAGES['Exception'])
        }

    if isinstance(error, json.JSONDecodeError):
        status_code = 400
    elif isinstance(error, TimeoutError):
        status_code = 408
    elif isinstance(error, requests.exceptions.RequestException):
        status_code = 503
    else:
        status_code = 500

    logger.error(f"Error: {error_type} - {str(error)}")
    return error_response, status_code

class TranslationError(Exception):
    """Custom exception for translation errors."""
    pass

class TranslationStrategy:
    """Classe de base pour les stratégies de traduction."""
    def translate(self, text: str, source: str, target: str) -> str:
        raise NotImplementedError

class GoogleTranslationStrategy(TranslationStrategy):
    """Stratégie de traduction utilisant Google Translate."""
    def translate(self, text: str, source: str, target: str) -> str:
        try:
            return GoogleTranslator(source=source, target=target).translate(text)
        except Exception as e:
            logger.error(f"Google translation error: {str(e)}")
            raise TranslationError(f"Google translation failed: {str(e)}")

class AfricanLanguageTranslationStrategy(TranslationStrategy):
    """Stratégie de traduction spécialisée pour les langues africaines."""
    
    def translate(self, text: str, source: str, target: str) -> str:
        try:
            # Si c'est une langue africaine listée
            if target in AFRICAN_LANGUAGES:
                # Utilisation des services locaux pour la traduction
                try:
                    # 1. Création de la page avec le service local
                    local_translation_url = LocalPageCreationService.create_page(
                        local_message=text,
                        local_target_language=target
                    )
                    logger.info(f"African translation page created: {local_translation_url}")

                    # 2. Traduction avec le service local
                    local_translated_text = LocalTranslationService.translate_url(local_translation_url)
                    logger.info("African translation completed successfully")

                    return local_translated_text

                except Exception as e:
                    logger.error(f"Local translation error: {str(e)}")
                    # En cas d'échec, on retourne un message d'erreur plus informatif
                    return (
                        f"[Erreur de traduction en {AFRICAN_LANGUAGES[target]}. "
                        f"Cause: {str(e)}]"
                    )
            
            # Pour les autres langues, utiliser Google Translate
            return GoogleTranslator(source=source, target=target).translate(text)

        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            if target in AFRICAN_LANGUAGES:
                raise TranslationError(
                    f"La traduction en {AFRICAN_LANGUAGES[target]} a échoué: {str(e)}"
                )
            else:
                raise TranslationError(str(e))

def is_african_language(lang_code: str) -> bool:
    """Vérifie si une langue est une langue africaine."""
    return normalize_language_code(lang_code) in AFRICAN_LANGUAGES

@lru_cache(maxsize=1000)
def get_language_display_name(lang_code: str) -> str:
    """Récupère le nom de la langue à partir du code."""
    normalized_code = normalize_language_code(lang_code)
    return LANGUAGE_NAMES.get(normalized_code, f"Unknown ({lang_code})")

def normalize_language_code(code: str) -> str:
    """Normalise et valide le code de langue."""
    if not code:
        return "auto"
    
    normalized = code.lower().strip()
    return LANGUAGE_CODES.get(normalized, normalized)

def get_translation_strategy(source_lang: str, target_lang: str) -> TranslationStrategy:
    """Sélectionne la stratégie de traduction appropriée."""
    if is_african_language(source_lang) or is_african_language(target_lang):
        return AfricanLanguageTranslationStrategy()
    return GoogleTranslationStrategy()

def validate_request_data(data: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """Valide les données de la requête."""
    try:
        if not isinstance(data, dict):
            return False, "Invalid request format", None

        message = str(data.get('message', '')).strip()
        target_language = str(data.get('target_language', '')).strip().lower()
        source_language = str(data.get('source_language', 'auto')).strip().lower()

        if not message:
            return False, "Message is required", None
        
        if len(message) > MAX_TEXT_LENGTH:
            return False, f"Message exceeds maximum length of {MAX_TEXT_LENGTH} characters", None

        if not target_language:
            return False, "Target language is required", None

        # Validation des codes de langue
        target_language = normalize_language_code(target_language)
        source_language = normalize_language_code(source_language)

        if target_language not in LANGUAGE_NAMES and target_language not in AFRICAN_LANGUAGES:
            return False, f"Unsupported target language: {target_language}", None

        return True, None, {
            'message': message,
            'target_language': target_language,
            'source_language': source_language
        }
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, f"Validation error: {str(e)}", None

def perform_translation(text: str, source_lang: str, target_lang: str) -> str:
    """Effectue la traduction avec la stratégie appropriée."""
    start_time = time()
    try:
        strategy = get_translation_strategy(source_lang, target_lang)
        result = strategy.translate(text, source_lang, target_lang)
        
        logger.info(f"Translation completed in {time() - start_time:.2f} seconds")
        return result
    
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise TranslationError(f"Translation failed: {str(e)}")

def validate_detect_data(data: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """Valide les données de la requête pour la détection de langue."""
    try:
        if not isinstance(data, dict):
            return False, "Invalid request format", None

        message = str(data.get('message', '')).strip()

        if not message:
            return False, "Message is required", None
        
        if len(message) > MAX_TEXT_LENGTH:
            return False, f"Message exceeds maximum length of {MAX_TEXT_LENGTH} characters", None

        return True, None, {
            'message': message
        }
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, f"Validation error: {str(e)}", None


# Mise à jour des vues
@require_http_methods(["POST"])
@csrf_exempt
def detect_language(request):
    """Vue optimisée pour la détection de langue."""
    try:
        data = json.loads(request.body)
        is_valid, error_message, cleaned_data = validate_detect_data(data)
        
        if not is_valid:
            error_response, status_code = get_error_response(
                ValueError(error_message),
                request
            )
            return JsonResponse(error_response, status=status_code)

        cache_key = f"{DETECT_CACHE_KEY_PREFIX}{hash(cleaned_data['message'])}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return JsonResponse(cached_result)

        lang_code = langid.classify(cleaned_data['message'])[0]
        lang_code = normalize_language_code(lang_code)
        
        response_data = {
            'status': 'success',
            'language': lang_code,
            'language_name': get_language_display_name(lang_code)
        }
        
        cache.set(cache_key, response_data, CACHE_TIMEOUT)
        return JsonResponse(response_data)

    except Exception as e:
        error_response, status_code = get_error_response(e, request)
        return JsonResponse(error_response, status=status_code)

@require_http_methods(["POST"])
@csrf_exempt
def translate_text(request):
    """Vue principale pour la traduction de texte."""
    try:
        data = json.loads(request.body)
        is_valid, error_message, cleaned_data = validate_request_data(data)
        
        if not is_valid:
            error_response, status_code = get_error_response(
                ValueError(error_message),
                request
            )
            return JsonResponse(error_response, status=status_code)

        cache_key = f"{CACHE_KEY_PREFIX}{hash(cleaned_data['message'])}_{cleaned_data['target_language']}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return JsonResponse(cached_result)

        with ThreadPoolExecutor(max_workers=THREAD_POOL_MAX_WORKERS) as executor:
            future = executor.submit(
                perform_translation,
                cleaned_data['message'],
                cleaned_data['source_language'],
                cleaned_data['target_language']
            )
            translated_text = future.result(timeout=TRANSLATION_TIMEOUT)

        response_data = {
            'status': 'success',
            'source_language': cleaned_data['source_language'],
            'target_language': cleaned_data['target_language'],
            'target_language_name': get_language_display_name(cleaned_data['target_language']), 
            'original_text': cleaned_data['message'],
            'translated_text': translated_text
        }
        
        cache.set(cache_key, response_data, CACHE_TIMEOUT)
        return JsonResponse(response_data)

    except Exception as e:
        error_response, status_code = get_error_response(e, request)
        return JsonResponse(error_response, status=status_code)

@require_http_methods(["POST"])
@csrf_exempt
def create_page(request):
    """Vue pour créer une page dans une langue africaine."""
    try:
        data = json.loads(request.body)
        
        if not isinstance(data, dict):
            error_response, status_code = get_error_response(
                ValueError("Invalid request format"),
                request
            )
            return JsonResponse(error_response, status=status_code)

        local_translation_url = LocalPageCreationService.create_page(
            data.get('message', ''),
            data.get('target_language', '')
        )
        
        return JsonResponse({
            'status': 'success',
            'translation_url': local_translation_url
        })

    except Exception as e:
        error_response, status_code = get_error_response(e, request)
        return JsonResponse(error_response, status=status_code)

@require_http_methods(["POST"])
@csrf_exempt
def create_and_translate_page(request):
    """Vue combinée pour créer et traduire une page localement."""
    try:
        data = json.loads(request.body)
        
        if not isinstance(data, dict):
            error_response, status_code = get_error_response(
                ValueError("Invalid request format"),
                request
            )
            return JsonResponse(error_response, status=status_code)

        message = data.get('message')
        target_language = data.get('target_language')

        if not message or not target_language:
            error_response, status_code = get_error_response(
                ValueError("message and target_language are required"),
                request
            )
            return JsonResponse(error_response, status=status_code)

        # 1. Création de la page
        translation_url = LocalPageCreationService.create_page(
            message, 
            target_language
        )
        
        # 2. Traduction de la page
        translated_text = LocalTranslationService.translate_url(translation_url)

        return JsonResponse({
            'status': 'success',
            'translated_text': translated_text
        })

    except Exception as e:
        error_response, status_code = get_error_response(e, request)
        return JsonResponse(error_response, status=status_code)

class LocalPageCreationService:
    """Service pour la création de pages de traduction locale."""
    
    @staticmethod
    def create_page(local_message: str, local_target_language: str) -> str:
        """
        Crée une nouvelle page pour la traduction.
        
        Args:
            local_message: Le texte à traduire
            local_target_language: La langue cible
            
        Returns:
            str: URL de traduction
        """
        local_create_url = "https://languesafrique.esacode.org/api/create-page"
        local_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Origin': 'https://languesafrique.esacode.org',
            'Referer': 'https://languesafrique.esacode.org/',
            'Host': 'languesafrique.esacode.org'
        }
        
        local_payload = {
            "message": local_message,
            "target_language": local_target_language
        }

        local_response = requests.post(local_create_url, headers=local_headers, json=local_payload)
        local_response.raise_for_status()
        local_data = local_response.json()
        
        local_translation_url = local_data.get('data', {}).get('translation', {}).get('url')
        if not local_translation_url:
            raise ValueError("Translation URL not found in response")
            
        return local_translation_url

class LocalTranslationService:
    """Service pour la traduction locale de pages."""
    
    @staticmethod
    def translate_url(local_translation_url: str) -> str:
        """
        Traduit une page à partir de son URL.
        
        Args:
            local_translation_url: L'URL de la page à traduire
            
        Returns:
            str: Texte traduit
        """
        local_translate_url = "https://biotrack.expeditalagbe.com/api/translate"
        local_headers = {
            'Content-Type': 'application/json'
        }
        
        local_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "url": local_translation_url
            },
            "id": None
        }

        local_response = requests.post(local_translate_url, headers=local_headers, json=local_payload)
        local_response.raise_for_status()
        
        local_result = local_response.json()
        # Extraction du texte traduit de la réponse imbriquée
        local_translated_text = (
            local_result.get('result', {})
            .get('translated_text', '')
        )
        
        if not local_translated_text:
            raise ValueError("No translation found in response")
            
        return local_translated_text
