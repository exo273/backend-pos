from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'
    verbose_name = 'Órdenes y Pagos'

    def ready(self):
        """Importar signals o tasks cuando la app esté lista"""
        try:
            import orders.tasks  # noqa
        except ImportError:
            pass
