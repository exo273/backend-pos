import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class KDSConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para Kitchen Display System (KDS).
    Muestra las órdenes en tiempo real en la cocina.
    """
    
    async def connect(self):
        # Unirse al grupo de KDS
        self.room_group_name = 'kds'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar órdenes activas al conectarse
        orders = await self.get_active_orders()
        await self.send(text_data=json.dumps({
            'type': 'initial_orders',
            'orders': orders
        }))
    
    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensajes del WebSocket (para actualizar estados desde KDS)"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            order_id = data.get('order_id')
            
            if action == 'update_status':
                new_status = data.get('status')
                await self.update_order_status(order_id, new_status)
                
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def order_update(self, event):
        """
        Enviar actualización de orden al KDS
        """
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'status': event['status'],
            'items': event['items'],
            'table': event['table'],
            'created_at': event['created_at'],
        }))
    
    @database_sync_to_async
    def get_active_orders(self):
        """Obtener órdenes activas para el KDS"""
        from .models import Order
        
        orders = Order.objects.filter(
            status__in=['pending', 'preparing']
        ).select_related('table').prefetch_related('items__menu_item')
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'table': order.table.number if order.table else None,
                'items': [
                    {
                        'id': item.id,
                        'menu_item_name': item.menu_item.name,
                        'quantity': item.quantity,
                        'notes': item.notes,
                    }
                    for item in order.items.all()
                ],
                'created_at': order.created_at.isoformat(),
            })
        
        return orders_data
    
    @database_sync_to_async
    def update_order_status(self, order_id, new_status):
        """Actualizar el estado de una orden desde el KDS"""
        from .models import Order
        
        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            
            # Broadcast a todos los clientes conectados
            order.broadcast_to_kds()
            
            return True
        except Order.DoesNotExist:
            return False


class OrderUpdateConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para actualizaciones generales de órdenes.
    Usado por el frontend del POS para recibir actualizaciones en tiempo real.
    """
    
    async def connect(self):
        # Unirse al grupo de actualizaciones de órdenes
        self.room_group_name = 'order_updates'
        
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
        """Recibir mensajes del WebSocket"""
        pass
    
    async def order_created(self, event):
        """Nueva orden creada"""
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'table': event.get('table'),
            'total': event['total'],
        }))
    
    async def order_status_changed(self, event):
        """Estado de orden cambió"""
        await self.send(text_data=json.dumps({
            'type': 'order_status_changed',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'old_status': event['old_status'],
            'new_status': event['new_status'],
        }))
    
    async def payment_received(self, event):
        """Pago recibido"""
        await self.send(text_data=json.dumps({
            'type': 'payment_received',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'payment_id': event['payment_id'],
            'amount': event['amount'],
            'payment_method': event['payment_method'],
        }))
