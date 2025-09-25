from django.conf import settings

def brand(request):
    """Expose brand settings to all templates.

    Available variables:
      - BRAND_NAME: Display name of the app
      - BRAND_TAGLINE: Optional small tagline (may be unused)
      - BRAND_LOGO: Path under STATIC_URL to the logo asset
    """
    return {
        'BRAND_NAME': getattr(settings, 'APP_BRAND_NAME', 'PumaSP'),
        'BRAND_TAGLINE': getattr(settings, 'APP_BRAND_TAGLINE', ''),
        'BRAND_LOGO': getattr(settings, 'APP_BRAND_LOGO', 'favicon.svg'),
    # Footer basics (customizable in settings/.env later)
    'FOOTER_CONTACT_EMAIL': getattr(settings, 'APP_CONTACT_EMAIL', 'soporte@example.com'),
    'FOOTER_CONTACT_LOCATION': getattr(settings, 'APP_CONTACT_LOCATION', 'Colombia'),
    }
