from django.http import HttpResponsePermanentRedirect

class CanonicalDomainMiddleware:
    """
    Middleware to enforce canonical domain (https://projectstore.pk).
    Redirects www.projectstore.pk to projectstore.pk via 301 Permanent Redirect.
    Fully compatible with cPanel / Passenger WSGI as well as Nginx.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0].lower()
        if host.startswith('www.'):
            canonical_host = host[4:]
            scheme = 'https' if request.is_secure() or request.META.get('HTTP_X_FORWARDED_PROTO') == 'https' else 'http'
            full_path = request.get_full_path()
            url = f"{scheme}://{canonical_host}{full_path}"
            return HttpResponsePermanentRedirect(url)
        return self.get_response(request)
