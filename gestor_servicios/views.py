from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from accounts.models import CustomUser
from oficinas.models import Office
from tickets.models import Ticket, TicketStatus
from django.db.models import Count, Q
from datetime import date
import json


def is_jefe(user):
    return user.is_authenticated and user.is_jefe


@login_required
@user_passes_test(is_jefe)
def dashboard(request):
    # Filtros por fecha y estado
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    statuses = request.GET.getlist('status')  # puede ser múltiple

    qs = Ticket.objects.all()

    # Validar y aplicar fechas
    start = None
    end = None
    try:
        if start_str:
            start = date.fromisoformat(start_str)
            qs = qs.filter(created_at__date__gte=start)
    except Exception:
        start = None
    try:
        if end_str:
            end = date.fromisoformat(end_str)
            qs = qs.filter(created_at__date__lte=end)
    except Exception:
        end = None

    # Validar y aplicar estados
    valid_status_codes = {choice.value for choice in TicketStatus}
    if statuses:
        statuses = [s for s in statuses if s in valid_status_codes]
        if statuses:
            qs = qs.filter(status__in=statuses)

    by_status = qs.values('status').annotate(total=Count('id')).order_by()
    by_office = qs.values('assigned_office__name').annotate(total=Count('id')).order_by('-total')
    pending_count = qs.filter(status__in=[TicketStatus.DRAFT, TicketStatus.ASSIGNED]).count()
    in_progress_count = qs.filter(status=TicketStatus.IN_PROGRESS).count()
    completed_count = qs.filter(status=TicketStatus.COMPLETED).count()
    # Dashboard JSON payload for charts
    status_data = []
    for row in by_status:
        code = row['status']
        try:
            display = TicketStatus(code).label
        except Exception:
            display = code
        status_data.append({
            'code': code,
            'display': display,
            'value': row['total'],
        })
    office_data = [
        {
            'label': (row['assigned_office__name'] or 'Sin oficina'),
            'value': row['total'],
        }
        for row in by_office
    ]
    dashboard_payload = {
        'statusData': status_data,
        'officeData': office_data,
    }
    # Choices de estado para UI
    status_choices = [
        {'code': c.value, 'label': c.label}
        for c in TicketStatus
    ]

    context = {
        'total_tickets': Ticket.objects.count(),  # total global
        'total_tickets_filtered': qs.count(),      # total según filtros
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'by_status': by_status,
        'by_office': by_office,
        'dashboard_payload': dashboard_payload,
        'status_choices': status_choices,
        'filters': {
            'start': start_str or '',
            'end': end_str or '',
            'statuses': statuses,
        }
    }
    return render(request, 'dashboard.html', context)


@login_required
def my_stats(request):
    user = request.user
    context = {}
    # Helper para mostrar etiquetas legibles de estado
    def label_status_rows(rows):
        labeled = []
        for row in rows:
            code = row['status']
            try:
                label = TicketStatus(code).label
            except Exception:
                label = code
            # Expose human label under 'status' to match templates (e.g., 'COMPLETADO'),
            # keep original code separately for potential programmatic use.
            labeled.append({
                'code': code,
                'status': label,
                'total': row['total'],
                'label': label,
                'value': row['total'],
            })
        return labeled
    
    # Put role and optional IDs for client-side logic
    stats_payload = { 'userRole': 'NONE' }
    if user.is_jefe:
        context['role'] = 'JEFE'
        # KPIs generales
        context['total_tickets'] = Ticket.objects.count()
        by_status_raw = Ticket.objects.values('status').annotate(total=Count('id')).order_by()
        context['by_status'] = label_status_rows(by_status_raw)
        stats_payload['userRole'] = 'JEFE'
        stats_payload['byStatus'] = context['by_status']
        
        by_office_raw = Ticket.objects.values('assigned_office__name').annotate(total=Count('id')).order_by('-total')
        by_office_formatted = [
            {'label': row['assigned_office__name'] or 'Sin oficina', 'value': row['total']} 
            for row in by_office_raw
        ]
        context['by_office'] = by_office_raw  # para mostrar en HTML
        stats_payload['byOffice'] = by_office_formatted
        
        # Agregar listas para filtros
        context['all_offices'] = Office.objects.all().order_by('name')
        context['all_technicians'] = CustomUser.objects.filter(role='TECNICO').select_related('office').order_by('first_name', 'last_name', 'username')
        # Choices de estado para checkboxes en UI
        context['status_choices'] = [
            { 'code': c.value, 'label': c.label }
            for c in TicketStatus
        ]
        
    elif user.is_supervisor:
        context['role'] = 'SUPERVISOR'
        # Solo de su oficina
        qs = Ticket.objects.filter(assigned_office=user.office)
        context['oficina'] = user.office
        context['office_id'] = getattr(user.office, 'id', None)
        context['asignados_oficina'] = qs.count()
        por_estado_raw = qs.values('status').annotate(total=Count('id')).order_by()
        context['por_estado'] = label_status_rows(por_estado_raw)
        stats_payload['userRole'] = 'SUPERVISOR'
        stats_payload['porEstado'] = context['por_estado']
        
        context['tecnicos_activos'] = CustomUser.objects.filter(office=user.office, role='TECNICO').count()
        context['mis_supervisados'] = qs.filter(supervisor=user).count()
        # Técnico con más tickets completados en su oficina
        if user.office:
            top_row = qs.filter(status='COMPLETED', technician__isnull=False) \
                .values('technician') \
                .annotate(total=Count('id')) \
                .order_by('-total') \
                .first()
            if top_row:
                try:
                    context['top_tecnico'] = CustomUser.objects.get(id=top_row['technician'])
                    context['top_tecnico_total'] = top_row['total']
                except CustomUser.DoesNotExist:
                    context['top_tecnico'] = None
                    context['top_tecnico_total'] = 0
            else:
                context['top_tecnico'] = None
                context['top_tecnico_total'] = 0
        else:
            context['top_tecnico'] = None
            context['top_tecnico_total'] = 0
            
        # Información adicional para supervisor
        if user.office:
            # Tickets del día para la oficina
            from datetime import date
            today = date.today()
            context['tickets_hoy_oficina'] = qs.filter(created_at__date=today).count()
            
            # Tickets urgentes de la oficina
            context['tickets_urgentes_oficina'] = qs.filter(
                priority__in=[TicketPriority.P4, TicketPriority.P5],  # Alta y Urgente
                status__in=['DRAFT', 'ASSIGNED', 'IN_PROGRESS']
            ).count()
            
            # Lista de técnicos con sus estadísticas básicas
            tecnicos_stats = []
            tecnicos_oficina = CustomUser.objects.filter(office=user.office, role='TECNICO')
            for tecnico in tecnicos_oficina:
                tecnico_tickets = Ticket.objects.filter(technician=tecnico)
                tecnicos_stats.append({
                    'tecnico': tecnico,
                    'asignados': tecnico_tickets.count(),
                    'completados': tecnico_tickets.filter(status='COMPLETED').count(),
                    'en_progreso': tecnico_tickets.filter(status='IN_PROGRESS').count()
                })
            context['tecnicos_stats'] = tecnicos_stats
            
            # Últimos tickets asignados a la oficina
            context['ultimos_tickets_oficina'] = qs.select_related('technician').order_by('-created_at')[:5]
            
    elif user.is_tecnico:
        context['role'] = 'TECNICO'
        qs = Ticket.objects.filter(technician=user)
        context['tech_id'] = user.id
        context['asignados'] = qs.count()
        por_estado_raw = qs.values('status').annotate(total=Count('id')).order_by()
        context['por_estado'] = label_status_rows(por_estado_raw)
        stats_payload['userRole'] = 'TECNICO'
        stats_payload['porEstado'] = context['por_estado']
        stats_payload['totalAsignados'] = context['asignados']
        
        context['completados'] = qs.filter(status='COMPLETED').count()
        context['pendientes_insumos'] = qs.filter(status='PENDING_SUPPLIES').count()
        stats_payload['completados'] = context['completados']
        
        # Información de oficina del técnico
        context['oficina'] = user.office
        if user.office:
            context['office_id'] = user.office.id
            # Compañeros técnicos en la misma oficina
            context['companeros_tecnicos'] = CustomUser.objects.filter(
                office=user.office, 
                role='TECNICO'
            ).exclude(id=user.id).count()
            # Supervisor de la oficina
            context['supervisor_oficina'] = user.office.supervisor
        else:
            context['office_id'] = None
            context['companeros_tecnicos'] = 0
            context['supervisor_oficina'] = None
        
        # Tickets del día actual (creados hoy)
        from datetime import date
        today = date.today()
        context['tickets_hoy'] = qs.filter(created_at__date=today).count()
        
        # Tickets urgentes asignados al técnico (sin completar)
        from tickets.models import TicketPriority
        context['tickets_urgentes'] = qs.filter(
            priority__in=[TicketPriority.P4, TicketPriority.P5],  # Alta y Urgente
            status__in=['DRAFT', 'ASSIGNED', 'IN_PROGRESS']
        ).count()
        
        # Últimos 3 tickets asignados
        context['ultimos_tickets'] = qs.select_related('assigned_office').order_by('-created_at')[:3]
    else:
        context['role'] = 'NONE'
        # Sin rol asignado
        context['mensaje'] = 'Aún no tienes un rol asignado.'
    context['stats_payload'] = stats_payload
    return render(request, 'my_stats.html', context)


@login_required
def my_stats_data(request):
    user = request.user
    # Build JSON payload per role with the same fields used in the template
    if user.is_jefe:
        # Obtener parámetros de filtro
        office_id = request.GET.get('office_id')
        technician_id = request.GET.get('technician_id')
        start_str = request.GET.get('start')
        end_str = request.GET.get('end')
        statuses = request.GET.getlist('status')  # puede ser múltiple
        
        # Base queryset
        tickets_qs = Ticket.objects.all()
        
        # Aplicar filtros
        if office_id and office_id != 'all':
            try:
                office_id = int(office_id)
                tickets_qs = tickets_qs.filter(assigned_office_id=office_id)
            except (ValueError, TypeError):
                pass
                
        if technician_id and technician_id != 'all':
            try:
                technician_id = int(technician_id)
                tickets_qs = tickets_qs.filter(technician_id=technician_id)
            except (ValueError, TypeError):
                pass
        # Fechas (ISO yyyy-mm-dd) sobre created_at__date
        from datetime import date
        try:
            if start_str:
                start = date.fromisoformat(start_str)
                tickets_qs = tickets_qs.filter(created_at__date__gte=start)
        except Exception:
            start = None
        try:
            if end_str:
                end = date.fromisoformat(end_str)
                tickets_qs = tickets_qs.filter(created_at__date__lte=end)
        except Exception:
            end = None
        # Estados
        valid_status_codes = {choice.value for choice in TicketStatus}
        if statuses:
            statuses = [s for s in statuses if s in valid_status_codes]
            if statuses:
                tickets_qs = tickets_qs.filter(status__in=statuses)
        
        by_status = list(tickets_qs.values('status').annotate(total=Count('id')).order_by())
        try:
            by_status = [
                {'status': TicketStatus(row['status']).label, 'total': row['total'], 'code': row['status']}
                for row in by_status
            ]
        except Exception:
            pass
        by_office = list(
            tickets_qs.values('assigned_office__name').annotate(total=Count('id')).order_by('-total')
        )

        # Distribuciones adicionales
        by_technician = []
        by_supervisor = []
        # Por técnico: tiene sentido cuando hay oficina concreta seleccionada
        if office_id and office_id != 'all':
            by_technician_qs = (
                tickets_qs
                .filter(technician__isnull=False)
                .values('technician_id',
                        'technician__first_name', 'technician__last_name', 'technician__username')
                .annotate(total=Count('id'))
                .order_by('-total')
            )
            for row in by_technician_qs:
                first = row.get('technician__first_name') or ''
                last = row.get('technician__last_name') or ''
                uname = row.get('technician__username') or ''
                full_name = (first + ' ' + last).strip() or uname
                by_technician.append({
                    'technician_id': row.get('technician_id'),
                    'name': full_name,
                    'total': row.get('total', 0),
                })
        # Por supervisor: incluir siempre (respetando otros filtros aplicados)
        try:
            by_supervisor_qs = (
                tickets_qs
                .filter(supervisor__isnull=False)
                .values('supervisor_id',
                        'supervisor__first_name', 'supervisor__last_name', 'supervisor__username')
                .annotate(total=Count('id'))
                .order_by('-total')
            )
            for row in by_supervisor_qs:
                first = row.get('supervisor__first_name') or ''
                last = row.get('supervisor__last_name') or ''
                uname = row.get('supervisor__username') or ''
                full_name = (first + ' ' + last).strip() or uname
                by_supervisor.append({
                    'supervisor_id': row.get('supervisor_id'),
                    'name': full_name,
                    'total': row.get('total', 0),
                })
        except Exception:
            by_supervisor = []
        
        # Estadísticas adicionales para filtros
        filter_info = {}
        if office_id and office_id != 'all':
            try:
                office = Office.objects.get(id=office_id)
                filter_info['office_name'] = office.name
            except Office.DoesNotExist:
                pass
                
        if technician_id and technician_id != 'all':
            try:
                tech = CustomUser.objects.get(id=technician_id)
                filter_info['technician_name'] = tech.get_full_name() or tech.username
            except CustomUser.DoesNotExist:
                pass
        # Añadir filtros de fecha/estado a la respuesta
        filters_payload = {
            'start': start_str or '',
            'end': end_str or '',
            'statuses': statuses or [],
            'office_id': office_id or 'all',
            'technician_id': technician_id or 'all',
        }
        
        payload = {
            'role': 'JEFE',
            'total_tickets': tickets_qs.count(),
            'by_status': by_status,
            'by_office': [
                {
                    'office': row['assigned_office__name'] or '(Sin oficina)',
                    'total': row['total']
                } for row in by_office
            ],
            'filter_info': filter_info,
            'filters': filters_payload,
        }
        if by_technician:
            payload['by_technician'] = by_technician
        if by_supervisor:
            payload['by_supervisor'] = by_supervisor
        return JsonResponse(payload)
    elif user.is_supervisor:
        qs = Ticket.objects.filter(assigned_office=user.office)
        por_estado = list(qs.values('status').annotate(total=Count('id')).order_by())
        try:
            por_estado = [
                {'status': TicketStatus(row['status']).label, 'total': row['total']}
                for row in por_estado
            ]
        except Exception:
            pass
        # top tecnico
        top_row = qs.filter(status='COMPLETED', technician__isnull=False).values('technician').annotate(total=Count('id')).order_by('-total').first()
        top_tecnico = None
        if top_row:
            try:
                tech = CustomUser.objects.get(id=top_row['technician'])
                top_tecnico = {
                    'id': tech.id,
                    'name': tech.get_full_name() or tech.username,
                    'email': tech.email,
                    'total': top_row['total'],
                }
            except CustomUser.DoesNotExist:
                top_tecnico = None
        return JsonResponse({
            'role': 'SUPERVISOR',
            'office': {'id': getattr(user.office, 'id', None), 'name': getattr(user.office, 'name', '')},
            'asignados_oficina': qs.count(),
            'por_estado': por_estado,
            'tecnicos_activos': CustomUser.objects.filter(office=user.office, role='TECNICO').count(),
            'mis_supervisados': qs.filter(supervisor=user).count(),
            'top_tecnico': top_tecnico,
        })
    elif user.is_tecnico:
        qs = Ticket.objects.filter(technician=user)
        por_estado = list(qs.values('status').annotate(total=Count('id')).order_by())
        try:
            por_estado = [
                {'status': TicketStatus(row['status']).label, 'total': row['total']}
                for row in por_estado
            ]
        except Exception:
            pass
        return JsonResponse({
            'role': 'TECNICO',
            'asignados': qs.count(),
            'por_estado': por_estado,
            'completados': qs.filter(status='COMPLETED').count(),
            'pendientes_insumos': qs.filter(status='PENDING_SUPPLIES').count(),
            'tech_id': user.id,
        })
    else:
        return JsonResponse({'role': 'NONE'})


@login_required
def get_technicians_by_office(request):
    """Endpoint para obtener técnicos filtrados por oficina"""
    if not request.user.is_jefe:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    office_id = request.GET.get('office_id')
    
    if office_id and office_id != 'all':
        try:
            office_id = int(office_id)
            # Incluir usuarios de la oficina que sean técnicos oficialmente
            # o que aparezcan como técnicos en tickets de esa oficina.
            tech_ids_from_tickets = Ticket.objects.filter(
                assigned_office_id=office_id,
                technician__isnull=False
            ).values_list('technician_id', flat=True).distinct()

            technicians = (
                CustomUser.objects
                .filter(office_id=office_id)
                .filter(Q(role='TECNICO') | Q(id__in=tech_ids_from_tickets))
                .select_related('office')
                .order_by('first_name', 'last_name', 'username')
            )
        except (ValueError, TypeError):
            technicians = CustomUser.objects.none()
    else:
        # Si no hay filtro o es 'all', devolver técnicos activos y aprobados
        technicians = (
            CustomUser.objects
            .filter(role='TECNICO')
            .select_related('office')
            .order_by('first_name', 'last_name', 'username')
        )
    
    technicians_data = []
    for tech in technicians:
        # Prefer full name only; if missing both first/last names, show a generic label
        name = tech.get_full_name().strip()
        if not name:
            name = 'Sin nombre'
        office_name = tech.office.name if tech.office else 'Sin oficina'
        technicians_data.append({
            'id': tech.id,
            'name': name,
            'office_name': office_name,
            'display_name': f"{name} ({office_name})",
            'last_first': f"{tech.last_name}, {tech.first_name}".strip(', ')
        })
    
    return JsonResponse({
        'technicians': technicians_data
    })