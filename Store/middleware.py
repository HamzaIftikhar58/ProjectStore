from django.http import HttpResponsePermanentRedirect

class CanonicalDomainMiddleware:
    """
    Middleware to enforce canonical non-WWW domain (https://projectstore.pk).
    Redirects www.projectstore.pk to projectstore.pk via 301 Permanent Redirect,
    unifying page authority and eliminating duplicate indexation.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            canonical_host = host[4:]
            # Enforce HTTPS on production or when behind secure proxy / cPanel SSL
            if (canonical_host in ('projectstore.pk', 'projectstore.isol.pk') 
                    or request.is_secure() 
                    or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https'
                    or request.META.get('HTTPS') == 'on'):
                scheme = 'https'
            else:
                scheme = 'https' if request.is_secure() else 'http'
            full_path = request.get_full_path()
            url = f"{scheme}://{canonical_host}{full_path}"
            return HttpResponsePermanentRedirect(url)
        return self.get_response(request)

