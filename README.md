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

### Ejecutar con Daphne (ASGI) — recomendado para Channels / WebSockets

Si tu proyecto usa Django Channels o necesitas probar WebSockets de forma realista,
usa Daphne (servidor ASGI). En desarrollo puedes ejecutarlo así:

```
.venv\Scripts\daphne.exe -b 127.0.0.1 -p 8000 gestor_servicios.asgi:application
```

Notas importantes relacionadas con ngrok y CSRF
- Para exponer el servidor local con ngrok y evitar errores CSRF (Origin checking failed)
	añade tus hostnames ngrok a la variable `NGROK_HOSTS` en el archivo `.env`:

```
NGROK_HOSTS=e4921ef9954a.ngrok-free.app
```

- El proyecto incluye soporte en `settings.py` para:
	- añadir `'.ngrok-free.app'` a `ALLOWED_HOSTS` cuando `DEBUG=1` y `ALLOW_NGROK=1` (por defecto),
	- poblar `CSRF_TRUSTED_ORIGINS` desde `NGROK_HOSTS` (se crea el origen con https://... automáticamente),
	- valores por defecto de desarrollo: `http://localhost` y `http://127.0.0.1` se añaden a `CSRF_TRUSTED_ORIGINS`.

- Si prefieres **no** permitir ngrok automáticamente, añade a `.env`:
```
ALLOW_NGROK=0
```

- Si por alguna razón quieres desactivar la comprobación CSRF en desarrollo (no recomendado),
	puedes usar la variable `DISABLE_CSRF=1` en `.env`. Esto removerá `CsrfViewMiddleware` cuando
	`DEBUG=1`. **No usar en entornos públicos ni producción.**

Verificación rápida (shell):
```
& .\.venv\Scripts\Activate.ps1
python manage.py shell
>>> from django.conf import settings
>>> settings.CSRF_TRUSTED_ORIGINS
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

