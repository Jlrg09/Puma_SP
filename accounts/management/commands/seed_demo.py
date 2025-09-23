from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Roles
from oficinas.models import Office
from tickets.models import Ticket, TicketPriority, TicketStatus, TicketNote, Evidence
from accounts.models import Notification
from io import BytesIO
from PIL import Image

class Command(BaseCommand):
    help = "Create demo data: offices, users (Jefe, Supervisores, Técnicos) and tickets"

    def handle(self, *args, **options):
        User = get_user_model()

        # Offices
        bogota, _ = Office.objects.get_or_create(name="Bogotá", defaults={"description": "Sede principal"})
        medellin, _ = Office.objects.get_or_create(name="Medellín", defaults={"description": "Sede regional"})
        cali, _ = Office.objects.get_or_create(name="Cali", defaults={"description": "Sede suroccidente"})
        barranquilla, _ = Office.objects.get_or_create(name="Barranquilla", defaults={"description": "Sede costa"})

        # Jefe
        jefe, created = User.objects.get_or_create(username="jefe", defaults={"email": "jefe@example.com"})
        # Ensure fields on every run (keep password when already exists)
        if created:
            jefe.set_password("jefe123")
        jefe.role = Roles.JEFE
        jefe.approved = True
        jefe.is_active = True
        jefe.first_name = "Jeferson"
        jefe.last_name = "Pérez"
        jefe.id_type = User.IdentificationType.CC
        jefe.id_number = jefe.id_number or "9001002001"
        jefe.birth_date = jefe.birth_date or "1980-05-12"
        jefe.phone = jefe.phone or "+57 300 000 0001"
        jefe.save()
        
        # Supervisores
        sup_bog, created = User.objects.get_or_create(username="sup_bog", defaults={"email": "sup_bog@example.com"})
        if created:
            sup_bog.set_password("demo1234")
        sup_bog.role = Roles.SUPERVISOR
        sup_bog.office = bogota
        sup_bog.approved = True
        sup_bog.is_active = True
        sup_bog.first_name = "Sofía"
        sup_bog.last_name = "Gómez"
        sup_bog.id_type = User.IdentificationType.CC
        sup_bog.id_number = sup_bog.id_number or "9001002002"
        sup_bog.birth_date = sup_bog.birth_date or "1987-03-21"
        sup_bog.phone = sup_bog.phone or "+57 300 000 0002"
        sup_bog.save()
        bogota.supervisor = sup_bog
        bogota.save()

        sup_med, created = User.objects.get_or_create(username="sup_med", defaults={"email": "sup_med@example.com"})
        if created:
            sup_med.set_password("demo1234")
        sup_med.role = Roles.SUPERVISOR
        sup_med.office = medellin
        sup_med.approved = True
        sup_med.is_active = True
        sup_med.first_name = "Daniel"
        sup_med.last_name = "Mejía"
        sup_med.id_type = User.IdentificationType.CC
        sup_med.id_number = sup_med.id_number or "9001002003"
        sup_med.birth_date = sup_med.birth_date or "1985-09-10"
        sup_med.phone = sup_med.phone or "+57 300 000 0003"
        sup_med.save()
        medellin.supervisor = sup_med
        medellin.save()

        # Técnicos
        tech1, created = User.objects.get_or_create(username="tecnico1", defaults={"email": "tecnico1@example.com"})
        if created:
            tech1.set_password("demo1234")
        tech1.role = Roles.TECNICO
        tech1.office = bogota
        tech1.approved = True
        tech1.is_active = True
        tech1.first_name = "Pedro"
        tech1.last_name = "López"
        tech1.id_type = User.IdentificationType.CC
        tech1.id_number = tech1.id_number or "9001002004"
        tech1.birth_date = tech1.birth_date or "1992-01-15"
        tech1.phone = tech1.phone or "+57 300 000 0004"
        tech1.save()

        tech2, created = User.objects.get_or_create(username="tecnico2", defaults={"email": "tecnico2@example.com"})
        if created:
            tech2.set_password("demo1234")
        tech2.role = Roles.TECNICO
        tech2.office = medellin
        tech2.approved = True
        tech2.is_active = True
        tech2.first_name = "María"
        tech2.last_name = "Rojas"
        tech2.id_type = User.IdentificationType.CC
        tech2.id_number = tech2.id_number or "9001002005"
        tech2.birth_date = tech2.birth_date or "1990-11-08"
        tech2.phone = tech2.phone or "+57 300 000 0005"
        tech2.save()

        tech3, created = User.objects.get_or_create(username="tecnico3", defaults={"email": "tecnico3@example.com"})
        if created:
            tech3.set_password("demo1234")
        tech3.role = Roles.TECNICO
        tech3.office = cali
        tech3.approved = True
        tech3.is_active = True
        tech3.first_name = "Andrés"
        tech3.last_name = "Cardona"
        tech3.id_type = User.IdentificationType.CC
        tech3.id_number = tech3.id_number or "9001002006"
        tech3.birth_date = tech3.birth_date or "1993-07-22"
        tech3.phone = tech3.phone or "+57 300 000 0006"
        tech3.save()

        tech4, created = User.objects.get_or_create(username="tecnico4", defaults={"email": "tecnico4@example.com"})
        if created:
            tech4.set_password("demo1234")
        tech4.role = Roles.TECNICO
        tech4.office = barranquilla
        tech4.approved = True
        tech4.is_active = True
        tech4.first_name = "Elena"
        tech4.last_name = "Córdoba"
        tech4.id_type = User.IdentificationType.CC
        tech4.id_number = tech4.id_number or "9001002007"
        tech4.birth_date = tech4.birth_date or "1995-04-30"
        tech4.phone = tech4.phone or "+57 300 000 0007"
        tech4.save()

        # Tickets
        base_tickets = [
                # Bogotá
                {"name": "Ana", "office": bogota, "desc": "PC no enciende", "prio": TicketPriority.P4, "status": TicketStatus.ASSIGNED, "sup": sup_bog, "tech": None},
                {"name": "Sofía", "office": bogota, "desc": "Actualización de software", "prio": TicketPriority.P3, "status": TicketStatus.DRAFT, "sup": sup_bog, "tech": None},
                {"name": "Pedro", "office": bogota, "desc": "Configuración de correo", "prio": TicketPriority.P2, "status": TicketStatus.IN_PROGRESS, "sup": sup_bog, "tech": tech1},
                {"name": "Lucía", "office": bogota, "desc": "Instalar impresora", "prio": TicketPriority.P1, "status": TicketStatus.COMPLETED, "sup": sup_bog, "tech": tech1},
                {"name": "Juan", "office": bogota, "desc": "Fallo de red", "prio": TicketPriority.P5, "status": TicketStatus.PENDING_SUPPLIES, "sup": sup_bog, "tech": tech1},

                # Medellín
                {"name": "Luis", "office": medellin, "desc": "Impresora atascada", "prio": TicketPriority.P2, "status": TicketStatus.IN_PROGRESS, "sup": sup_med, "tech": tech2},
                {"name": "Daniela", "office": medellin, "desc": "Pantalla parpadea", "prio": TicketPriority.P3, "status": TicketStatus.ASSIGNED, "sup": sup_med, "tech": None},
                {"name": "María", "office": medellin, "desc": "Teclado no responde", "prio": TicketPriority.P2, "status": TicketStatus.COMPLETED, "sup": sup_med, "tech": tech2},
                {"name": "Jorge", "office": medellin, "desc": "Lento al iniciar", "prio": TicketPriority.P1, "status": TicketStatus.DRAFT, "sup": sup_med, "tech": None},
                {"name": "Camila", "office": medellin, "desc": "Copia de seguridad", "prio": TicketPriority.P3, "status": TicketStatus.PENDING_SUPPLIES, "sup": sup_med, "tech": tech2},

                # Cali
                {"name": "Andrés", "office": cali, "desc": "No hay sonido", "prio": TicketPriority.P2, "status": TicketStatus.ASSIGNED, "sup": None, "tech": tech3},
                {"name": "Carolina", "office": cali, "desc": "Instalar Office", "prio": TicketPriority.P3, "status": TicketStatus.IN_PROGRESS, "sup": None, "tech": tech3},
                {"name": "Felipe", "office": cali, "desc": "Error de disco", "prio": TicketPriority.P5, "status": TicketStatus.COMPLETED, "sup": None, "tech": tech3},
                {"name": "Natalia", "office": cali, "desc": "Configurar VPN", "prio": TicketPriority.P4, "status": TicketStatus.DRAFT, "sup": None, "tech": None},
                {"name": "Paula", "office": cali, "desc": "Actualizar drivers", "prio": TicketPriority.P2, "status": TicketStatus.PENDING_SUPPLIES, "sup": None, "tech": tech3},

                # Barranquilla
                {"name": "Ricardo", "office": barranquilla, "desc": "WiFi intermitente", "prio": TicketPriority.P3, "status": TicketStatus.ASSIGNED, "sup": None, "tech": tech4},
                {"name": "Elena", "office": barranquilla, "desc": "Cámara no funciona", "prio": TicketPriority.P2, "status": TicketStatus.IN_PROGRESS, "sup": None, "tech": tech4},
                {"name": "Pablo", "office": barranquilla, "desc": "Recuperar archivos", "prio": TicketPriority.P4, "status": TicketStatus.COMPLETED, "sup": None, "tech": tech4},
                {"name": "Valentina", "office": barranquilla, "desc": "Instalar antivirus", "prio": TicketPriority.P1, "status": TicketStatus.DRAFT, "sup": None, "tech": None},
                {"name": "Santiago", "office": barranquilla, "desc": "Fallo de teclado", "prio": TicketPriority.P2, "status": TicketStatus.PENDING_SUPPLIES, "sup": None, "tech": tech4},
        ]

        # If DB has no tickets, seed the base set once
        if not Ticket.objects.exists():
            for t in base_tickets:
                Ticket.objects.create(
                    requester_name=t["name"],
                    requester_office=t["office"],
                    requester_office_text=t["office"].name,
                    description=t["desc"],
                    priority=t["prio"],
                    assigned_office=t["office"],
                    supervisor=t["sup"],
                    technician=t["tech"],
                    status=t["status"],
                )

        # Ensure at least 30 tickets by generating more demo items if needed
        target = 30
        current = Ticket.objects.count()
        if current < target:
            offices = [bogota, medellin, cali, barranquilla]
            office_sup = {
                bogota.id: sup_bog,
                medellin.id: sup_med,
                cali.id: None,
                barranquilla.id: None,
            }
            office_tech = {
                bogota.id: tech1,
                medellin.id: tech2,
                cali.id: tech3,
                barranquilla.id: tech4,
            }
            statuses = [
                TicketStatus.DRAFT,
                TicketStatus.ASSIGNED,
                TicketStatus.IN_PROGRESS,
                TicketStatus.PENDING_SUPPLIES,
                TicketStatus.COMPLETED,
            ]
            priorities = [
                TicketPriority.P1,
                TicketPriority.P2,
                TicketPriority.P3,
                TicketPriority.P4,
                TicketPriority.P5,
            ]
            n_to_add = target - current
            for i in range(n_to_add):
                office = offices[i % len(offices)]
                status = statuses[i % len(statuses)]
                prio = priorities[i % len(priorities)]
                sup = office_sup.get(office.id)
                tech = office_tech.get(office.id)
                Ticket.objects.create(
                    requester_name=f"Demo{i:02}",
                    requester_office=office,
                    requester_office_text=office.name,
                    description=f"[DEMO] Tarea {i} en {office.name}",
                    priority=prio,
                    assigned_office=office,
                    supervisor=sup,
                    technician=tech if status != TicketStatus.DRAFT else None,
                    status=status,
                )

        # Add demo notes/evidences/notifications to a few tickets
        some_tickets = list(Ticket.objects.order_by('-id')[:5])
        for idx, tk in enumerate(some_tickets):
            # Note
            TicketNote.objects.get_or_create(
                ticket=tk,
                author=tk.technician or tk.supervisor,
                text=f"Nota de prueba {idx+1} para ticket {tk.id}",
            )
            # Evidence - generate a tiny image in-memory
            try:
                img = Image.new('RGB', (200, 120), color=(30 + idx * 20, 64, 175))
                bio = BytesIO()
                img.save(bio, format='PNG')
                bio.seek(0)
                # Use a deterministic name; ImageField needs a file-like with name
                from django.core.files.base import ContentFile
                content = ContentFile(bio.read(), name=f"demo_{tk.id}_{idx}.png")
                if not tk.evidences.exists():
                    Evidence.objects.create(ticket=tk, image=content)
            except Exception:
                pass
            # Notification
            if tk.supervisor:
                Notification.objects.get_or_create(
                    recipient=tk.supervisor,
                    ticket=tk,
                    defaults={"text": f"Actualización del ticket #{tk.id}"},
                )

        # Summary output
        self.stdout.write(self.style.SUCCESS(
            f"Demo data created/updated. Offices: {Office.objects.count()} | Users: {User.objects.count()} | Tickets: {Ticket.objects.count()}"
        ))
