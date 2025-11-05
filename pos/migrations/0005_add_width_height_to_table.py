# Generated manually on 2025-11-05

from django.db import migrations


def add_width_height_columns(apps, schema_editor):
    """Agregar columnas width y height si no existen y la tabla existe"""
    with schema_editor.connection.cursor() as cursor:
        # Primero verificar si la tabla 'tables' existe
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tables'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        # Si la tabla no existe, salir sin hacer nada (las migraciones anteriores la crearán)
        if not table_exists:
            return
        
        # Verificar si las columnas ya existen
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'tables'
            AND COLUMN_NAME IN ('width', 'height')
        """)
        existing_columns = cursor.fetchone()[0]
        
        # Solo agregar si no existen
        if existing_columns == 0:
            cursor.execute("""
                ALTER TABLE tables
                ADD COLUMN width INT NOT NULL DEFAULT 1 COMMENT 'Ancho en celdas de cuadrícula',
                ADD COLUMN height INT NOT NULL DEFAULT 1 COMMENT 'Alto en celdas de cuadrícula'
            """)
        elif existing_columns == 1:
            # Verificar cuál existe y agregar la que falta
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'tables'
                AND COLUMN_NAME IN ('width', 'height')
            """)
            existing = cursor.fetchone()[0]
            if existing == 'width':
                cursor.execute("""
                    ALTER TABLE tables
                    ADD COLUMN height INT NOT NULL DEFAULT 1 COMMENT 'Alto en celdas de cuadrícula'
                """)
            else:
                cursor.execute("""
                    ALTER TABLE tables
                    ADD COLUMN width INT NOT NULL DEFAULT 1 COMMENT 'Ancho en celdas de cuadrícula'
                """)


class Migration(migrations.Migration):

    dependencies = []  # Sin dependencias para evitar conflictos
    
    operations = [
        migrations.RunPython(add_width_height_columns, migrations.RunPython.noop),
    ]
