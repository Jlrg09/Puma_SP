# Gestor de Servicios

Aplicación web en Django para gestión de servicios con tres roles: Jefe, Supervisor y Técnico. Incluye registro con aprobación, gestión de oficinas, creación y asignación de tickets, actualización de estados, observaciones y evidencias.

## Requisitos
- Windows (PowerShell)
- Python 3.11+ (probado con 3.13)

## Pasos de instalación (PowerShell)
1. Crear entorno virtual:
```
py -3 -m venv .venv
```
2. Activar (opcional si usas los comandos completos):
```
.\.venv\Scripts\Activate.ps1
```
3. Instalar dependencias:
```
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```
4. Variables de entorno (copiar y ajustar):
```
Copy-Item .env.example .env
```
5. Migraciones y superusuario:
```
& ".\.venv\Scripts\python.exe" manage.py migrate
& ".\.venv\Scripts\python.exe" manage.py createsuperuser
```
6. Ejecutar servidor:
```
& ".\.venv\Scripts\python.exe" manage.py runserver
```

## Flujo de roles
- Registro: el usuario queda "pendiente" (approved=false) y sólo puede ver la pantalla de espera.
- Jefe: aprueba usuarios, asigna roles y oficinas, crea oficinas y tickets. Puede editar/eliminar oficinas y usuarios.
- Supervisor: asigna tickets de su oficina a técnicos o a sí mismo, ve cargas de trabajo.
- Técnico: ve sus tickets, actualiza estado (en curso, pendiente de insumos, completado), agrega observaciones y evidencias.

## Migración a PostgreSQL
1. Instalar psycopg (opcional, no incluido por defecto):
```
& ".\.venv\Scripts\python.exe" -m pip install psycopg[binary]
```
2. Configurar `.env`:
```
DATABASE_URL=postgres://usuario:password@localhost:5432/gestor
DB_SSL_REQUIRE=0
DEBUG=0
ALLOWED_HOSTS=127.0.0.1,localhost
```
3. Ejecutar migraciones normalmente. `dj-database-url` tomará la URL.

## Estructura
- `accounts`: Usuario personalizado, registro y aprobación, middleware de aprobación, gestión de usuarios (Jefe).
- `oficinas`: CRUD de oficinas y asignación de supervisor.
- `tickets`: Modelos de tickets, notas y evidencias; creación (Jefe), asignación (Supervisor), actualización (Técnico).

## Notas
- Archivos subidos se guardan en `media/` (crear carpeta si subes evidencias).
- Estáticos en `static/` (ya configurado).
- Idioma: Español, Zona horaria: America/Bogota.

