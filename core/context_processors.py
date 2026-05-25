from django.conf import settings

def ads_settings(request):
    """Injects ad-related settings into templates."""
    return {
        'ADS_ENABLED': getattr(settings, 'ADS_ENABLED', False),
        'ADS_PROVIDER': getattr(settings, 'ADS_PROVIDER', 'mock'),
        'ADSENSE_CLIENT': getattr(settings, 'ADSENSE_CLIENT', ''),
        'ADS_SLOTS': getattr(settings, 'ADS_SLOTS', {}),
    }
