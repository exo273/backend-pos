import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class TableStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para actualizaciones en tiempo real del estado de las mesas.
    """
    
    async def connect(self):
        # Unirse al grupo de mesas
        self.room_group_name = 'tables'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensajes del WebSocket (opcional)"""
        pass
    
    async def table_status_update(self, event):
        """
        Enviar actualización de estado de mesa al WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'table_status_update',
            'table_id': event['table_id'],
            'table_number': event['table_number'],
            'zone': event['zone'],
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))
