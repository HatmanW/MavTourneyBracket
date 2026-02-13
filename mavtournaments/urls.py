# mavtournaments/urls.py
from django.urls import path
from . import views

app_name = "tournaments"

urlpatterns = [
    # Tournaments
    path("", views.index, name="index"),
    path("create/", views.create_tournament, name="create"),
    path("<int:pk>/delete/", views.delete_tournament, name="delete"),

    # Teams
    path("<int:pk>/teams/", views.teams, name="teams"),
    path("<int:pk>/teams/<int:team_id>/", views.team_detail, name="team_detail"),
    path("<int:pk>/teams/add/", views.add_team, name="add_team"),
    path("<int:pk>/teams/<int:team_id>/join/", views.team_join, name="team_join"),
    path("<int:pk>/teams/<int:team_id>/leave/", views.team_leave, name="team_leave"),

    # Bracket + views
    path("<int:pk>/", views.bracket, name="bracket"),
    path("<int:pk>/ui/", views.bracket, name="bracket_ui"),  # alias for old templates
    path("<int:pk>/data/", views.bracket_data, name="bracket_data"),  # JSON for bracket_view.html

    # Seeding (explicit names — recommended)
    path("<int:pk>/seed/random/", views.seed_random, name="seed_random"),
    path("<int:pk>/seed/power/", views.seed_power, name="seed_power"),

    # Match actions
    path("<int:pk>/advance/<int:match_id>/", views.advance_match, name="advance_match"),
    path("<int:pk>/set-winner/<int:match_id>/<int:team_id>/", views.set_winner, name="set_winner"),  # alias for templates

    path("<int:pk>/move/", views.move_team, name="move_team"),

    # Team Builder + CSV
    path("<int:pk>/team-builder/", views.team_builder, name="team_builder"),
    path("<int:pk>/bulk-teams/", views.bulk_teams, name="bulk_teams"),
    path("<int:pk>/bulk-teams/preview/", views.bulk_teams_preview, name="bulk_teams_preview"),
    path("<int:pk>/bulk-teams/confirm/", views.bulk_teams_confirm, name="bulk_teams_confirm"),
    path("<int:pk>/csv-template/", views.csv_template, name="csv_template"),
]
