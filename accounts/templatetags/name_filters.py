from django import template

register = template.Library()

@register.filter(name='last_first')
def last_first(user):
    """Render user's name as "Apellidos, Nombres" with fallbacks.
    Accepts a CustomUser or any object with first_name/last_name/username.
    """
    if not user:
        return ''
    first = (getattr(user, 'first_name', '') or '').strip()
    last = (getattr(user, 'last_name', '') or '').strip()
    if last and first:
        return f"{last}, {first}"
    if last:
        return last
    if first:
        return first
    # Fallback minimal visible text (avoid username in UI)
    return 'Sin nombre'

@register.filter(name='first_last')
def first_last(user):
    """Render user's name as "Nombre Apellido" with sensible fallbacks."""
    if not user:
        return ''
    first = (getattr(user, 'first_name', '') or '').strip()
    last = (getattr(user, 'last_name', '') or '').strip()
    full = ' '.join([p for p in [first, last] if p])
    return full if full else 'Sin nombre'