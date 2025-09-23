from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='tickets_index'),
    path('crear/', views.create, name='ticket_create'),
    path('<int:ticket_id>/asignar/', views.assign, name='ticket_assign'),
    path('<int:ticket_id>/actualizar/', views.update_status, name='ticket_update'),
    path('<int:ticket_id>/detalle/', views.ticket_detail, name='ticket_detail'),
    path('<int:ticket_id>/nota/', views.add_note, name='ticket_add_note'),
    path('<int:ticket_id>/evidencia/', views.add_evidence, name='ticket_add_evidence'),
]