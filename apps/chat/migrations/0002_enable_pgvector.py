
from django.db import migrations
from django.contrib.postgres.operations import CreateExtension

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        CreateExtension('vector'),
    ]
