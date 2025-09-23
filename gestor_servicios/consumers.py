import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)

class StatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Obtener el usuario de la sesión
            user = self.scope.get('user')
            
            # Log para debug
            logger.info(f"WebSocket connection attempt from user: {user}")
            
            # Permitir conexión pero verificar autenticación después
            await self.accept()
            
            # Verificar autenticación
            if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Authentication required'
                }))
                await self.close()
                return
            
            # Almacenar información del usuario
            self.user = user
            self.groups_to_join = []
            
            # Grupo general del usuario
            self.user_group = f'user_{user.id}'
            self.groups_to_join.append(self.user_group)
            
            # Obtener información adicional del usuario de forma asíncrona
            user_info = await self.get_user_info(user)
            
            # Grupos por rol usando la información obtenida de forma asíncrona
            if user_info.get('is_jefe'):
                self.groups_to_join.append('stats_jefes')
                logger.info(f"User {user.username} added to stats_jefes group")
            
            if user_info.get('is_supervisor'):
                office_id = user_info.get('office_id')
                if office_id:
                    self.groups_to_join.append(f'stats_office_{office_id}')
                    logger.info(f"User {user.username} added to stats_office_{office_id} group")
            
            if user_info.get('is_tecnico'):
                self.groups_to_join.append(f'stats_tech_{user.id}')
                logger.info(f"User {user.username} added to stats_tech_{user.id} group")
            
            # Unirse a los grupos
            for group in self.groups_to_join:
                await self.channel_layer.group_add(group, self.channel_name)
            
            # Enviar confirmación de conexión exitosa
            await self.send(text_data=json.dumps({
                'type': 'connected',
                'message': 'WebSocket connected successfully',
                'groups': self.groups_to_join
            }))
            
            logger.info(f"WebSocket connected for user {user.username} with groups: {self.groups_to_join}")
            
        except Exception as e:
            logger.error(f"Error in WebSocket connect: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Connection failed'
            }))
            await self.close()

    @database_sync_to_async
    def get_user_info(self, user):
        """Obtener información del usuario de forma asíncrona"""
        try:
            info = {
                'is_jefe': getattr(user, 'is_jefe', False),
                'is_supervisor': getattr(user, 'is_supervisor', False),
                'is_tecnico': getattr(user, 'is_tecnico', False),
                'office_id': None
            }
            
            # Obtener la oficina si existe de forma segura
            try:
                if hasattr(user, 'office') and user.office:
                    info['office_id'] = user.office.id
            except Exception:
                # Ignorar errores de acceso a la oficina
                pass
                
            return info
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {
                'is_jefe': False,
                'is_supervisor': False,
                'is_tecnico': False,
                'office_id': None
            }

    async def disconnect(self, close_code):
        try:
            # Salir de todos los grupos
            for group in getattr(self, 'groups_to_join', []):
                await self.channel_layer.group_discard(group, self.channel_name)
            
            user = getattr(self, 'user', None)
            if user:
                logger.info(f"WebSocket disconnected for user {user.username}")
        except Exception as e:
            logger.error(f"Error in WebSocket disconnect: {e}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            # Log para debug
            logger.info(f"Received WebSocket message: {message_type}")
            
            # Responder con pong si recibe ping
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    # Handler para eventos de estadísticas
    async def stats_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'stats_update',
                'data': event.get('data', {})
            }))
        except Exception as e:
            logger.error(f"Error sending stats update: {e}")
    
    # Handler para notificaciones
    async def notification_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'notification_update',
                'data': event.get('data', {})
            }))
        except Exception as e:
            logger.error(f"Error sending notification update: {e}")
