from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# Este módulo es principalmente para procesar eventos entrantes
# Las tareas principales están en orders/tasks.py

@shared_task(name='catalog_mirror.sync_catalog')
def sync_catalog():
    """
    Tarea programada para sincronizar todo el catálogo
    desde el microservicio de operaciones (opcional).
    
    Normalmente la sincronización es evento-driven,
    pero esta tarea puede usarse como backup.
    """
    logger.info("Sincronización manual del catálogo iniciada")
    
    # Esta sería una sincronización completa via API REST
    # al microservicio de operaciones (implementar si se necesita)
    
    logger.warning("Sincronización manual no implementada. Use eventos en tiempo real.")
    return False
