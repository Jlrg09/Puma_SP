from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.http import JsonResponse
from accounts.models import CustomUser
from oficinas.models import Office
from tickets.models import Ticket, TicketStatus
from django.db.models import Count
import json


def is_jefe(user):
    return user.is_authenticated and user.is_jefe


@login_required
@user_passes_test(is_jefe)
def dashboard(request):
    by_status = Ticket.objects.values('status').annotate(total=Count('id')).order_by()
    by_office = Ticket.objects.values('assigned_office__name').annotate(total=Count('id')).order_by('-total')
    pending_count = Ticket.objects.filter(status__in=[TicketStatus.DRAFT, TicketStatus.ASSIGNED]).count()
    in_progress_count = Ticket.objects.filter(status=TicketStatus.IN_PROGRESS).count()
    completed_count = Ticket.objects.filter(status=TicketStatus.COMPLETED).count()
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
    context = {
        'total_tickets': Ticket.objects.count(),
        'pending_count': pending_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'by_status': by_status,
        'by_office': by_office,
        'dashboard_payload': dashboard_payload,
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
        by_status = list(Ticket.objects.values('status').annotate(total=Count('id')).order_by())
        try:
            by_status = [
                {'status': TicketStatus(row['status']).label, 'total': row['total']}
                for row in by_status
            ]
        except Exception:
            pass
        by_office = list(
            Ticket.objects.values('assigned_office__name').annotate(total=Count('id')).order_by('-total')
        )
        return JsonResponse({
            'role': 'JEFE',
            'total_tickets': Ticket.objects.count(),
            'by_status': by_status,
            'by_office': [
                {
                    'office': row['assigned_office__name'] or '(Sin oficina)',
                    'total': row['total']
                } for row in by_office
            ],
        })
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