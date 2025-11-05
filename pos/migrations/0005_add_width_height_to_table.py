# Generated manually on 2025-11-05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0004_remove_table_unique_table_number_per_zone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='width',
            field=models.IntegerField(default=1, help_text='Ancho en celdas de cuadrícula', verbose_name='Ancho'),
        ),
        migrations.AddField(
            model_name='table',
            name='height',
            field=models.IntegerField(default=1, help_text='Alto en celdas de cuadrícula', verbose_name='Alto'),
        ),
    ]
