from django.shortcuts import render
from django.core.exceptions import PermissionDenied

class FriendlyPermissionDeniedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except PermissionDenied:
            # If the user is authenticated but lacks permission, show a friendly 403 page
            status = 403
            return render(request, '403.html', status=status)
