from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Roles
from oficinas.models import Office
from tickets.models import Ticket, TicketPriority, TicketStatus, TicketNote, Evidence
from accounts.models import Notification
from io import BytesIO
from PIL import Image
import random
from datetime import timedelta
from django.utils import timezone
from django.core.management import call_command
from django.db import utils as db_utils

class Command(BaseCommand):
    help = "Create demo data: offices, users (Jefe, Supervisores, Técnicos) and many tickets"

    def add_arguments(self, parser):
        parser.add_argument('--tickets', type=int, default=200, help='Total tickets to ensure in DB (default: 200)')
        parser.add_argument('--months', type=int, default=6, help='Distribute tickets across last N months (default: 6)')
        parser.add_argument('--tech-per-office', type=int, default=6, help='Technicians to create per office (minimum baseline will be kept)')
        parser.add_argument('--no-evidence', action='store_true', help='Skip generating evidence images')
        parser.add_argument('--reset', action='store_true', help='Delete existing demo tickets and notes/evidence before seeding')

    def handle(self, *args, **options):
        User = get_user_model()
        total_tickets_target = max(1, options['tickets'])
        months = max(1, options['months'])
        tech_per_office_target = max(1, options['tech_per_office'])
        skip_evidence = options['no_evidence']
        do_reset = options['reset']

        # Ensure DB schema is up-to-date
        try:
            call_command('migrate', interactive=False, verbosity=0)
        except Exception:
            pass

        if do_reset:
            # Danger zone: only delete Ticket-related demo entities
            self.stdout.write(self.style.WARNING('Resetting demo tickets, notes and evidences...'))
            for qs in (Evidence.objects, TicketNote.objects, Ticket.objects):
                try:
                    qs.all().delete()
                except (db_utils.OperationalError, db_utils.ProgrammingError, Exception):
                    # Tables may not exist yet; ignore
                    pass

        # Offices
        bogota, _ = Office.objects.get_or_create(name="Bogotá", defaults={"description": "Sede principal"})
        medellin, _ = Office.objects.get_or_create(name="Medellín", defaults={"description": "Sede regional"})
        cali, _ = Office.objects.get_or_create(name="Cali", defaults={"description": "Sede suroccidente"})
        barranquilla, _ = Office.objects.get_or_create(name="Barranquilla", defaults={"description": "Sede costa"})
        cartagena, _ = Office.objects.get_or_create(name="Cartagena", defaults={"description": "Sede Caribe"})
        bucaramanga, _ = Office.objects.get_or_create(name="Bucaramanga", defaults={"description": "Sede nororiente"})

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

        # Supervisores adicionales
        sup_cali, created = User.objects.get_or_create(username="sup_cali", defaults={"email": "sup_cali@example.com"})
        if created:
            sup_cali.set_password("demo1234")
        sup_cali.role = Roles.SUPERVISOR
        sup_cali.office = cali
        sup_cali.approved = True
        sup_cali.is_active = True
        sup_cali.first_name = "Carla"
        sup_cali.last_name = "Zapata"
        sup_cali.save()
        cali.supervisor = sup_cali
        cali.save()

        sup_baq, created = User.objects.get_or_create(username="sup_baq", defaults={"email": "sup_baq@example.com"})
        if created:
            sup_baq.set_password("demo1234")
        sup_baq.role = Roles.SUPERVISOR
        sup_baq.office = barranquilla
        sup_baq.approved = True
        sup_baq.is_active = True
        sup_baq.first_name = "Diego"
        sup_baq.last_name = "Cano"
        sup_baq.save()
        barranquilla.supervisor = sup_baq
        barranquilla.save()

        sup_car, created = User.objects.get_or_create(username="sup_car", defaults={"email": "sup_car@example.com"})
        if created:
            sup_car.set_password("demo1234")
        sup_car.role = Roles.SUPERVISOR
        sup_car.office = cartagena
        sup_car.approved = True
        sup_car.is_active = True
        sup_car.first_name = "Valeria"
        sup_car.last_name = "Pardo"
        sup_car.save()
        cartagena.supervisor = sup_car
        cartagena.save()

        sup_bga, created = User.objects.get_or_create(username="sup_bga", defaults={"email": "sup_bga@example.com"})
        if created:
            sup_bga.set_password("demo1234")
        sup_bga.role = Roles.SUPERVISOR
        sup_bga.office = bucaramanga
        sup_bga.approved = True
        sup_bga.is_active = True
        sup_bga.first_name = "Julián"
        sup_bga.last_name = "Mora"
        sup_bga.save()
        bucaramanga.supervisor = sup_bga
        bucaramanga.save()

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

        # Crear más técnicos por oficina según objetivo
        offices_for_tech = [bogota, medellin, cali, barranquilla, cartagena, bucaramanga]
        for off in offices_for_tech:
            existing = User.objects.filter(role=Roles.TECNICO, office=off).count()
            to_add = max(0, tech_per_office_target - existing)
            for i in range(to_add):
                uname = f"tec_{off.name.lower()[0:3]}_{existing + i + 1}"
                u, created = User.objects.get_or_create(username=uname, defaults={"email": f"{uname}@example.com"})
                if created:
                    u.set_password("demo1234")
                u.role = Roles.TECNICO
                u.office = off
                u.first_name = f"Tec {off.name[:3]}"
                u.last_name = f"#{existing + i + 1}"
                u.approved = True
                u.is_active = True
                u.save()

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

        # Ensure a larger number of tickets distributed over time
        target = total_tickets_target
        current = Ticket.objects.count()
        if current < target:
            offices = [bogota, medellin, cali, barranquilla, cartagena, bucaramanga]
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
            # pool de técnicos por oficina
            tech_pool = {
                off.id: list(User.objects.filter(role=Roles.TECNICO, office=off))
                for off in offices
            }
            sup_pool = {
                off.id: getattr(off, 'supervisor', None)
                for off in offices
            }
            now = timezone.now()
            for i in range(n_to_add):
                office = random.choice(offices)
                status = random.choice(statuses)
                prio = random.choice(priorities)
                sup = sup_pool.get(office.id)
                techs = tech_pool.get(office.id) or []
                tech = random.choice(techs) if techs else None
                # Distribuir fecha de creación en los últimos N meses
                delta_days = random.randint(0, months * 30)
                created_at = now - timedelta(days=delta_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                tk = Ticket.objects.create(
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
                # Sobrescribir timestamps si es posible (direct DB update)
                Ticket.objects.filter(id=tk.id).update(created_at=created_at, updated_at=created_at)

        # Add demo notes/evidences/notifications to a sample of recent tickets
        some_tickets = list(Ticket.objects.order_by('-id')[:min(20, Ticket.objects.count())])
        for idx, tk in enumerate(some_tickets):
            # Note
            TicketNote.objects.get_or_create(
                ticket=tk,
                author=tk.technician or tk.supervisor,
                text=f"Nota de prueba {idx+1} para ticket {tk.id}",
            )
            # Evidence - generate a tiny image in-memory
            if not skip_evidence:
                try:
                    img = Image.new('RGB', (200, 120), color=(30 + (idx * 12) % 180, 64, 175))
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
