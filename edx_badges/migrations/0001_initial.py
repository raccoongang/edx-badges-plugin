# Generated by Django 3.2.19 on 2023-10-30 15:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('badges', '0004_badgeclass_badgr_server_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('revoked', 'Revoked'), ('replaced', 'Replaced')], max_length=255)),
                ('credly_badge_id', models.CharField(blank=True, max_length=255)),
                ('assertion', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='badge_status', to='badges.badgeassertion')),
            ],
            options={
                'verbose_name_plural': 'Badge statuses',
            },
        ),
    ]
