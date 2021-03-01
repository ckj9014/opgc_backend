# Generated by Django 2.2.17 on 2021-03-01 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('githubs', '0003_auto_20210214_0120'),
    ]

    operations = [
        migrations.AddField(
            model_name='githubuser',
            name='total_stargazers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='repository',
            name='stargazers_count',
            field=models.IntegerField(default=0),
        ),
    ]
