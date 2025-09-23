from django.shortcuts import redirect
from django.urls import reverse

class ApprovalRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if request.user.is_authenticated:
            allow_paths = {reverse('waiting'), reverse('logout'), reverse('login')}
            if not request.user.approved and path not in allow_paths and not path.startswith('/admin/'):
                return redirect('waiting')
        return self.get_response(request)
