# Generated by Django 4.1.7 on 2023-02-19 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0007_alter_order_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='document',
            field=models.FileField(blank=True, null=True, upload_to='order_documents/%Y/%m/%d/'),
        ),
    ]
