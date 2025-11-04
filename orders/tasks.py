from celery import shared_task
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


@shared_task(name='orders.publish_order_paid')
def publish_order_paid(order_id):
    """
    Publica evento ORDEN_PAGADA al microservicio de operaciones
    para que descuente el stock de los productos/recetas utilizados.
    """
    from .models import Order
    from menu.models import MenuItemComponent
    from catalog_mirror.models import MirroredProduct, MirroredRecipe
    import pika
    from django.conf import settings
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Recopilar información de stock a descontar
        stock_deductions = {
            'products': [],
            'recipes': []
        }
        
        for order_item in order.items.all():
            # Obtener componentes del menu item
            for component in order_item.menu_item.components.all():
                quantity_to_deduct = component.quantity * order_item.quantity
                
                if component.component_type == 'product':
                    stock_deductions['products'].append({
                        'product_id': component.product_id,
                        'quantity': float(quantity_to_deduct),
                    })
                elif component.component_type == 'recipe':
                    stock_deductions['recipes'].append({
                        'recipe_id': component.recipe_id,
                        'quantity': float(quantity_to_deduct),
                    })
        
        # Publicar evento a RabbitMQ
        event_data = {
            'event_type': 'ORDEN_PAGADA',
            'order_id': order.id,
            'order_number': order.order_number,
            'timestamp': order.completed_at.isoformat() if order.completed_at else None,
            'stock_deductions': stock_deductions
        }
        
        # Conectar a RabbitMQ
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declarar exchange
        channel.exchange_declare(
            exchange='restaurant_events',
            exchange_type='topic',
            durable=True
        )
        
        # Publicar mensaje
        channel.basic_publish(
            exchange='restaurant_events',
            routing_key='pos.order.paid',
            body=json.dumps(event_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
                content_type='application/json'
            )
        )
        
        connection.close()
        
        logger.info(f"Evento ORDEN_PAGADA publicado para orden {order.order_number}")
        return True
        
    except Order.DoesNotExist:
        logger.error(f"Orden {order_id} no encontrada")
        return False
    except Exception as e:
        logger.error(f"Error al publicar evento ORDEN_PAGADA: {str(e)}")
        raise


@shared_task(name='orders.listen_operations_events')
def listen_operations_events():
    """
    Escucha eventos del microservicio de operaciones
    (PRODUCT_STOCK_UPDATED, RECIPE_UPDATED) para actualizar catalog_mirror.
    
    Esta tarea debe ejecutarse como un worker persistente.
    """
    import pika
    from django.conf import settings
    
    def callback(ch, method, properties, body):
        """Procesa mensajes recibidos"""
        try:
            data = json.loads(body)
            event_type = data.get('event_type')
            
            if event_type == 'PRODUCT_STOCK_UPDATED':
                process_product_update.delay(data)
            elif event_type == 'RECIPE_UPDATED':
                process_recipe_update.delay(data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error procesando evento: {str(e)}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    try:
        # Conectar a RabbitMQ
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declarar exchange
        channel.exchange_declare(
            exchange='restaurant_events',
            exchange_type='topic',
            durable=True
        )
        
        # Declarar cola
        queue_name = 'pos_service_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind a eventos de operaciones
        channel.queue_bind(
            exchange='restaurant_events',
            queue=queue_name,
            routing_key='operations.product.*'
        )
        channel.queue_bind(
            exchange='restaurant_events',
            queue=queue_name,
            routing_key='operations.recipe.*'
        )
        
        # Consumir mensajes
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        
        logger.info("Comenzando a escuchar eventos del microservicio de operaciones...")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Deteniendo consumidor de eventos...")
        if connection:
            connection.close()
    except Exception as e:
        logger.error(f"Error en listener de eventos: {str(e)}")
        raise


@shared_task(name='orders.process_product_update')
def process_product_update(event_data):
    """
    Procesa evento PRODUCT_STOCK_UPDATED del microservicio de operaciones
    y actualiza el catálogo espejo local.
    """
    from catalog_mirror.models import MirroredProduct
    from menu.models import MenuItemComponent
    
    try:
        product_id = event_data.get('product_id')
        product_data = event_data.get('product_data', {})
        
        # Actualizar o crear producto espejo
        mirrored_product, created = MirroredProduct.objects.update_or_create(
            original_id=product_id,
            defaults={
                'name': product_data.get('name', ''),
                'sku': product_data.get('sku', ''),
                'unit_cost': Decimal(str(product_data.get('unit_cost', 0))),
                'current_stock': Decimal(str(product_data.get('current_stock', 0))),
                'unit_of_measure': product_data.get('unit_of_measure', 'unidad'),
                'is_active': product_data.get('is_active', True),
            }
        )
        
        action = "creado" if created else "actualizado"
        logger.info(f"Producto espejo {mirrored_product.name} {action}")
        
        # Actualizar cached_unit_cost en componentes que usan este producto
        components = MenuItemComponent.objects.filter(
            component_type='product',
            product_id=product_id
        )
        
        for component in components:
            component.cached_unit_cost = mirrored_product.unit_cost
            component.save()
            
            # Recalcular costo del menu item
            component.menu_item.calculate_cost()
        
        if components.exists():
            logger.info(f"Actualizados {components.count()} componentes de menú")
        
        return True
        
    except Exception as e:
        logger.error(f"Error procesando actualización de producto: {str(e)}")
        raise


@shared_task(name='orders.process_recipe_update')
def process_recipe_update(event_data):
    """
    Procesa evento RECIPE_UPDATED del microservicio de operaciones
    y actualiza el catálogo espejo local.
    """
    from catalog_mirror.models import MirroredRecipe
    from menu.models import MenuItemComponent
    
    try:
        recipe_id = event_data.get('recipe_id')
        recipe_data = event_data.get('recipe_data', {})
        
        # Actualizar o crear receta espejo
        mirrored_recipe, created = MirroredRecipe.objects.update_or_create(
            original_id=recipe_id,
            defaults={
                'name': recipe_data.get('name', ''),
                'production_cost': Decimal(str(recipe_data.get('production_cost', 0))),
                'yield_quantity': Decimal(str(recipe_data.get('yield_quantity', 1))),
                'yield_unit': recipe_data.get('yield_unit', 'porción'),
                'is_active': recipe_data.get('is_active', True),
            }
        )
        
        # Calcular costo por unidad
        mirrored_recipe.calculate_cost_per_unit()
        
        action = "creada" if created else "actualizada"
        logger.info(f"Receta espejo {mirrored_recipe.name} {action}")
        
        # Actualizar cached_unit_cost en componentes que usan esta receta
        components = MenuItemComponent.objects.filter(
            component_type='recipe',
            recipe_id=recipe_id
        )
        
        for component in components:
            component.cached_unit_cost = mirrored_recipe.cost_per_unit
            component.save()
            
            # Recalcular costo del menu item
            component.menu_item.calculate_cost()
        
        if components.exists():
            logger.info(f"Actualizados {components.count()} componentes de menú")
        
        return True
        
    except Exception as e:
        logger.error(f"Error procesando actualización de receta: {str(e)}")
        raise
