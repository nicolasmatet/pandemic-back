# Generated by Django 3.0.5 on 2020-05-02 11:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='MapLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('location_type', models.CharField(max_length=8)),
                ('population', models.IntegerField()),
                ('x', models.FloatField()),
                ('y', models.FloatField()),
                ('map', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maplocations', to='pandemic.Map')),
                ('neighbors', models.ManyToManyField(related_name='rel_neighbors', to='pandemic.MapLocation')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('taken', models.BooleanField(default=True)),
                ('ready', models.BooleanField(default=False)),
                ('role', models.IntegerField(null=True)),
                ('order', models.IntegerField(default=0)),
                ('location', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='map_states', to='pandemic.MapLocation')),
            ],
        ),
        migrations.CreateModel(
            name='PlayRoom',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=16)),
                ('has_started', models.BooleanField(default=False)),
                ('outbreaks', models.IntegerField(default=0)),
                ('epidemics', models.IntegerField(default=0)),
                ('phase', models.IntegerField(default=0)),
                ('epidemics_to_solve', models.IntegerField(default=0)),
                ('player_actions', models.IntegerField(default=0)),
                ('current_player', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='current_player', to='pandemic.Player')),
                ('map', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pandemic.Map')),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='playroom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='players', to='pandemic.PlayRoom'),
        ),
        migrations.CreateModel(
            name='MapState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('research_center', models.BooleanField(default=False)),
                ('location', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='location_map_state', to='pandemic.MapLocation')),
                ('playroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mapstates', to='pandemic.PlayRoom')),
            ],
        ),
        migrations.AddField(
            model_name='map',
            name='starting_location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='starting_map', to='pandemic.MapLocation'),
        ),
        migrations.CreateModel(
            name='DiseaseStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disease_type', models.IntegerField()),
                ('disease_status', models.IntegerField(default=0)),
                ('playroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pandemic.PlayRoom')),
            ],
        ),
        migrations.CreateModel(
            name='Disease',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('disease_type', models.IntegerField()),
                ('disease_count', models.IntegerField(default=0)),
                ('map_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pandemic.MapState')),
            ],
        ),
        migrations.CreateModel(
            name='CardsLocationDeck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('type', models.CharField(max_length=16)),
                ('location', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='pandemic.MapLocation')),
            ],
        ),
        migrations.CreateModel(
            name='CardLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=None)),
                ('position', models.CharField(default='deck', max_length=8)),
                ('card', models.OneToOneField(max_length=32, on_delete=django.db.models.deletion.CASCADE, related_name='card_location', to='pandemic.CardsLocationDeck')),
                ('player', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hand', to='pandemic.Player')),
                ('playroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playroom_card_locations', to='pandemic.PlayRoom')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CardInfection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('order', models.IntegerField()),
                ('position', models.CharField(default='deck', max_length=8)),
                ('location', models.OneToOneField(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='location_card_infections', to='pandemic.MapLocation')),
                ('playroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_infections', to='pandemic.PlayRoom')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
