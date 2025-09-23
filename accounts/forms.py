from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label=_('Nombres'), max_length=150, required=True)
    last_name = forms.CharField(label=_('Apellidos'), max_length=150, required=True)
    email = forms.EmailField(label=_('Correo electrónico'), required=True)
    id_type = forms.ChoiceField(label=_('Tipo de identificación'), choices=CustomUser.IdentificationType.choices, required=True)
    id_number = forms.CharField(label=_('Número de identificación'), max_length=32, required=True)
    birth_date = forms.DateField(label=_('Fecha de nacimiento'), required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    phone = forms.CharField(label=_('Teléfono'), max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "id_type", "id_number", "birth_date", "phone", "password1", "password2")

    def clean_id_number(self):
        value = self.cleaned_data.get('id_number', '').strip()
        if not value.isdigit():
            raise forms.ValidationError(_('El número de identificación debe contener solo dígitos.'))
        # Unicidad: también cubierta por constraint, pero validamos temprano
        if CustomUser.objects.filter(id_number=value).exists():
            raise forms.ValidationError(_('Este número de identificación ya está registrado.'))
        return value

    def save(self, commit=True):
        user: CustomUser = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.id_type = self.cleaned_data['id_type']
        user.id_number = self.cleaned_data['id_number']
        user.birth_date = self.cleaned_data['birth_date']
        user.phone = self.cleaned_data.get('phone')
        if commit:
            user.save()
        return user
