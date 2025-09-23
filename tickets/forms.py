from django import forms
from .models import Ticket, TicketStatus, TicketPriority


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            'requester_name',
            'requester_office_text',
            'description',
            'priority',
            'assigned_office',
        ]
        labels = {
            'requester_name': 'Nombre del solicitante',
            'requester_office_text': 'Oficina que solicita',
            'description': 'Descripción del servicio',
            'priority': 'Prioridad',
            'assigned_office': 'Oficina asignada',
        }


class SupervisorAssignForm(forms.Form):
    technician_id = forms.IntegerField(widget=forms.HiddenInput, required=False)


class TechnicianUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['equipment_code', 'status']
        labels = {
            'equipment_code': 'Código del equipo',
            'status': 'Estado',
        }

    note = forms.CharField(
        label='Nota (requerida si Pendiente por insumos)',
        widget=forms.Textarea,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow technician-settable statuses
        allowed = [TicketStatus.IN_PROGRESS, TicketStatus.PENDING_SUPPLIES, TicketStatus.COMPLETED]
        self.fields['status'].widget = forms.Select(choices=[(s, TicketStatus(s).label) for s in allowed])

    def clean_status(self):
        value = self.cleaned_data['status']
        allowed = {TicketStatus.IN_PROGRESS, TicketStatus.PENDING_SUPPLIES, TicketStatus.COMPLETED}
        if value not in allowed:
            raise forms.ValidationError('Estado no permitido para técnico')
        return value

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        note = cleaned.get('note', '').strip()
        if status == TicketStatus.PENDING_SUPPLIES and not note:
            self.add_error('note', 'Debes especificar los insumos necesarios en la nota.')
        return cleaned


class TicketNoteForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label='Observación / Necesidad')


class EvidenceForm(forms.Form):
    image = forms.ImageField(label='Imagen')
