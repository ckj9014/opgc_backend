# Generated by Django 2.2.17 on 2021-02-14 03:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('githubs', '0003_auto_20210214_0120'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('type', models.CharField(max_length=200)),
                ('ranking', models.SmallIntegerField(default=0)),
                ('score', models.IntegerField(default=0)),
                ('github_user', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='githubs.GithubUser')),
            ],
            options={
                'verbose_name': 'user_rank',
            },
        ),
    ]
