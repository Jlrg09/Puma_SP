from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='oficinas_index'),
    path('crear/', views.create, name='oficina_create'),
    path('<int:office_id>/editar/', views.edit, name='oficina_edit'),
    path('<int:office_id>/eliminar/', views.delete, name='oficina_delete'),
]