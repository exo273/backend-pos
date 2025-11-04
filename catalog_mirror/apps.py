from django.apps import AppConfig


class CatalogMirrorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog_mirror'
    verbose_name = 'Catálogo Espejo'

    def ready(self):
        """Importar signals o tasks cuando la app esté lista"""
        try:
            import catalog_mirror.tasks  # noqa
        except ImportError:
            pass
