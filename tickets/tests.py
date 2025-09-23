from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from oficinas.models import Office
from tickets.models import Ticket, TicketStatus, TicketPriority


User = get_user_model()


class TicketFlowTests(TestCase):
    def setUp(self):
        self.of1 = Office.objects.create(name='Of1')
        self.of2 = Office.objects.create(name='Of2')
        self.jefe = User.objects.create_user(username='jefe', password='pass12345', approved=True, role='JEFE')
        self.sup1 = User.objects.create_user(username='sup1', password='pass12345', approved=True, role='SUPERVISOR', office=self.of1)
        self.sup2 = User.objects.create_user(username='sup2', password='pass12345', approved=True, role='SUPERVISOR', office=self.of2)
        self.tech1 = User.objects.create_user(username='t1', password='pass12345', approved=True, role='TECNICO', office=self.of1)
        self.ticket = Ticket.objects.create(
            requester_name='Juan', requester_office=self.of1, description='Arreglar PC',
            priority=TicketPriority.P3, assigned_office=self.of1, status=TicketStatus.ASSIGNED
        )

    def test_supervisor_can_assign_only_in_own_office(self):
        # Supervisor de otra oficina no debe poder cargar la página de asignación del ticket de of1
        self.client.login(username='sup2', password='pass12345')
        resp = self.client.get(reverse('ticket_assign', args=[self.ticket.id]))
        self.assertEqual(resp.status_code, 404)

        # Supervisor correcto sí puede
        self.client.login(username='sup1', password='pass12345')
        resp = self.client.get(reverse('ticket_assign', args=[self.ticket.id]))
        self.assertEqual(resp.status_code, 200)

    def test_technician_can_set_allowed_status(self):
        # asignamos técnico primero
        self.ticket.technician = self.tech1
        self.ticket.save()
        self.client.login(username='t1', password='pass12345')
        # Estado permitido
        resp = self.client.post(reverse('ticket_update', args=[self.ticket.id]), data={'equipment_code': 'EQ-1', 'status': TicketStatus.IN_PROGRESS})
        self.assertEqual(resp.status_code, 302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.IN_PROGRESS)

# Create your tests here.
