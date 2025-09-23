from django.core.exceptions import PermissionDenied
from functools import wraps


def jefe_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(user, 'is_jefe', False):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def supervisor_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(user, 'is_supervisor', False):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def tecnico_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not getattr(user, 'is_tecnico', False):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
