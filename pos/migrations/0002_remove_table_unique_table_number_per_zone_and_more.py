# Generated manually based on production database
# This migration already exists in production

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='table',
            name='unique_table_number_per_zone',
        ),
        migrations.AddConstraint(
            model_name='table',
            constraint=models.UniqueConstraint(fields=('zone', 'number'), name='unique_table_number_per_zone'),
        ),
    ]
