# Generated manually on 2025-11-05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
            ],
            options={
                'verbose_name': 'Zona',
                'verbose_name_plural': 'Zonas',
                'db_table': 'zones',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(verbose_name='Número')),
                ('capacity', models.IntegerField(verbose_name='Capacidad')),
                ('status', models.CharField(choices=[('available', 'Disponible'), ('occupied', 'Ocupada'), ('reserved', 'Reservada')], default='available', max_length=20, verbose_name='Estado')),
                ('position_x', models.IntegerField(blank=True, help_text='Posición X en la cuadrícula', null=True, verbose_name='Posición X')),
                ('position_y', models.IntegerField(blank=True, help_text='Posición Y en la cuadrícula', null=True, verbose_name='Posición Y')),
                ('width', models.IntegerField(default=1, help_text='Ancho en celdas de cuadrícula', verbose_name='Ancho')),
                ('height', models.IntegerField(default=1, help_text='Alto en celdas de cuadrícula', verbose_name='Alto')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tables', to='pos.zone', verbose_name='Zona')),
            ],
            options={
                'verbose_name': 'Mesa',
                'verbose_name_plural': 'Mesas',
                'db_table': 'tables',
                'ordering': ['zone', 'number'],
            },
        ),
        migrations.AddConstraint(
            model_name='table',
            constraint=models.UniqueConstraint(fields=('zone', 'number'), name='unique_table_number_per_zone'),
        ),
    ]
