# mavtournaments/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .services.bracket_builder import generate_single_elim, set_winner as advance_winner
from .models import Tournament, Team, Match
from .forms import TournamentForm, TeamForm    # keep your custom forms if any


def _ctx_tournament(t, **extra):
    """Standard context helper: always supply both 'tournament' and 't'."""
    base = {"tournament": t, "t": t}
    base.update(extra)
    return base


# --------------------------
# Tournaments
# --------------------------
@login_required
def index(request):
    qs = Tournament.objects.order_by("-id")
    return render(request, "mavtournaments/index.html", {"tournaments": qs})

@login_required
@permission_required("mavtournaments.add_tournament", raise_exception=True)
def create_tournament(request):
    if request.method == "POST":
        form = TournamentForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f'Created tournament "{t.name}".')
            return redirect("tournaments:bracket", pk=t.pk)
    else:
        form = TournamentForm()
    return render(request, "mavtournaments/create.html", {"form": form})

@login_required
@permission_required("mavtournaments.delete_tournament", raise_exception=True)
def delete_tournament(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    if request.method == "POST":
        name = t.name
        t.delete()
        messages.success(request, f'Deleted tournament "{name}".')
        return redirect("tournaments:index")
    return render(request, "mavtournaments/confirm_delete.html", {"t": t})


# --------------------------
# Bracket
# --------------------------
@login_required
def bracket(request, pk):
    t = get_object_or_404(Tournament, pk=pk)

    # --- detect if teams changed since bracket was built
    team_ids = set(t.teams.values_list("id", flat=True))

    bracket_team_ids = set(t.matches.values_list("team1_id", flat=True)) | set(
        t.matches.values_list("team2_id", flat=True)
    )
    bracket_team_ids.discard(None)

    # "Started" = any match where BOTH teams existed and a winner was recorded
    bracket_started = t.matches.filter(
        winner__isnull=False,
        team1__isnull=False,
        team2__isnull=False,
    ).exists()

    needs_rebuild = (
        (t.rounds.exists() and team_ids != bracket_team_ids)
        or (not t.rounds.exists() and len(team_ids) >= 2)
        or (t.rounds.exists() and len(team_ids) < 2)
    )

    if needs_rebuild:
        if bracket_started:
            messages.warning(
                request,
                "Teams changed, but the bracket already has played matches, so it was not regenerated.",
            )
        else:
            generate_single_elim(t)

    rounds = t.rounds.prefetch_related("matches").all()

    pending_matches = (
        t.matches.select_related("round", "team1", "team2")
        .filter(
            winner__isnull=True,
            team1__isnull=False,
            team2__isnull=False,
        )
        .order_by("round__index", "slot")
    )

    round_count = rounds.count()
    max_matches = max((r.matches.count() for r in rounds), default=1)
    svg_w = max(400, round_count * 350 + 350)
    svg_h = max(300, max_matches * 120 + 120)

    return render(request, "mavtournaments/bracket.html", {
        "t": t,
        "rounds": rounds,
        "svg_w": svg_w,
        "svg_h": svg_h,
        "pending_matches": pending_matches,
        "can_advance": request.user.has_perm("mavtournaments.advance_match"),
    })

def _viewer_opponent(team_id, winner_id):
    payload = {"id": team_id}

    if team_id is not None and winner_id is not None:
        won = team_id == winner_id
        payload["score"] = 1 if won else 0
        payload["result"] = "win" if won else "loss"

    return payload


@login_required
def bracket_data(request, pk):
    t = get_object_or_404(Tournament, pk=pk)

    matches_qs = (
        t.matches.select_related("round", "team1", "team2", "winner")
        .order_by("round__index", "slot")
    )

    participants = [
        {
            "id": team.id,
            "name": team.name,
        }
        for team in t.teams.order_by("name")
    ]

    team_count = max(2, t.teams.count())
    bracket_size = 1 << (team_count - 1).bit_length()

    stages = [
        {
            "id": t.id,
            "name": t.name,
            "number": 1,
            "type": "single_elimination",
            "settings": {
                "size": bracket_size,
            },
        }
    ]

    matches = []
    for m in matches_qs:
        matches.append({
            "id": m.id,
            "number": m.slot + 1,
            "stage_id": t.id,
            "group_id": 0,
            "round_id": m.round.index,   # 0-based is fine here
            "child_count": 0,            # single match, not Bo3/Bo5
            "status": 4 if m.winner_id else 1,
            "opponent1": _viewer_opponent(m.team1_id, m.winner_id),
            "opponent2": _viewer_opponent(m.team2_id, m.winner_id),
        })

    data = {
        "stages": stages,
        "matches": matches,
        "matchGames": [],
        "participants": participants,
    }

    return JsonResponse(data)


# --------------------------
# Teams
# --------------------------
@login_required
def teams(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    teams_qs = Team.objects.filter(tournament=t).order_by("name")
    return render(request, "mavtournaments/teams.html", _ctx_tournament(t, teams=teams_qs))

@login_required
def team_detail(request, pk, team_id):
    t = get_object_or_404(Tournament, pk=pk)
    team = get_object_or_404(Team, pk=team_id, tournament=t)
    return render(request, "mavtournaments/team_detail.html", _ctx_tournament(t, team=team))

@login_required
def team_join(request, pk, team_id):
    # TODO: add actual membership logic
    t = get_object_or_404(Tournament, pk=pk)
    messages.success(request, "Joined team (placeholder).")
    return redirect("tournaments:team_detail", pk=t.pk, team_id=team_id)

@login_required
def team_leave(request, pk, team_id):
    # TODO: add actual membership logic
    t = get_object_or_404(Tournament, pk=pk)
    messages.info(request, "Left team (placeholder).")
    return redirect("tournaments:team_detail", pk=t.pk, team_id=team_id)

@login_required
@permission_required(
    # allow either the built-in model perm OR your custom manage_teams
    perm=("mavtournaments.add_team",), raise_exception=True
)
def add_team(request, pk):
    # also allow your custom manage_teams if present
    if (not request.user.has_perm("mavtournaments.add_team")
        and not request.user.has_perm("mavtournaments.manage_teams")):
        return redirect("tournaments:teams", pk=pk)

    t = get_object_or_404(Tournament, pk=pk)

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("tournaments:teams", pk=t.pk)

    form = TeamForm(request.POST)
    if form.is_valid():
        team = form.save(commit=False)
        team.tournament = t
        team.save()
        messages.success(request, f'Team "{team.name}" added.')
    else:
        # keep the form errors across the redirect (simple way: flash them)
        messages.error(request, "Please provide a valid team name.")

    return redirect("tournaments:teams", pk=t.pk)

# --------------------------
# Seeding
# --------------------------
@login_required
@permission_required("mavtournaments.manage_seeding", raise_exception=True)
def seed_random(request, pk):
    t = get_object_or_404(Tournament, pk=pk)

    bracket_started = t.matches.filter(
        winner__isnull=False,
        team1__isnull=False,
        team2__isnull=False,
    ).exists()

    if bracket_started:
        messages.warning(request, "Bracket already has played matches; seeding blocked.")
        return redirect("tournaments:bracket", pk=t.pk)

    generate_single_elim(t, seed_method="RANDOM")
    messages.success(request, "Random seeding executed.")
    return redirect("tournaments:bracket", pk=t.pk)


@login_required
@permission_required("mavtournaments.manage_seeding", raise_exception=True)
def seed_power(request, pk):
    t = get_object_or_404(Tournament, pk=pk)

    bracket_started = t.matches.filter(
        winner__isnull=False,
        team1__isnull=False,
        team2__isnull=False,
    ).exists()

    if bracket_started:
        messages.warning(request, "Bracket already has played matches; seeding blocked.")
        return redirect("tournaments:bracket", pk=t.pk)

    generate_single_elim(t, seed_method="POWER")
    messages.success(request, "Power seeding executed.")
    return redirect("tournaments:bracket", pk=t.pk)


# --------------------------
# Matches / flow
# --------------------------
def _apply_match_winner(request, t, match_id, team_id):
    match = get_object_or_404(
        Match.objects.select_related("team1", "team2", "winner", "round"),
        pk=match_id,
        tournament=t,
    )
    team = get_object_or_404(Team, pk=team_id, tournament=t)

    if match.winner_id:
        if match.winner_id == team.id:
            messages.info(request, "That winner is already recorded.")
        else:
            messages.warning(
                request,
                "This match already has a winner. Editing completed results is not implemented yet.",
            )
        return redirect("tournaments:bracket", pk=t.pk)

    if team.id not in {match.team1_id, match.team2_id}:
        messages.error(request, "Selected team is not part of this match.")
        return redirect("tournaments:bracket", pk=t.pk)

    if not match.team1_id or not match.team2_id:
        messages.error(
            request,
            "This match is missing a team. It cannot be advanced manually.",
        )
        return redirect("tournaments:bracket", pk=t.pk)

    advance_winner(match, team, cascade=True)
    messages.success(request, f"{team.name} advanced from {match.label()}.")
    return redirect("tournaments:bracket", pk=t.pk)


@login_required
@permission_required("mavtournaments.advance_match", raise_exception=True)
def advance_match(request, pk, match_id):
    t = get_object_or_404(Tournament, pk=pk)

    winner_id = request.POST.get("winner_id") or request.GET.get("winner_id")
    if not winner_id:
        messages.error(request, "No winner was selected for that match.")
        return redirect("tournaments:bracket", pk=t.pk)

    return _apply_match_winner(request, t, match_id, winner_id)


@login_required
@permission_required("mavtournaments.advance_match", raise_exception=True)
def set_winner(request, pk, match_id, team_id):
    t = get_object_or_404(Tournament, pk=pk)
    return _apply_match_winner(request, t, match_id, team_id)

@login_required
@permission_required("mavtournaments.manage_teams", raise_exception=True)
def move_team(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    messages.info(request, "Moved team (placeholder).")
    return redirect("tournaments:teams", pk=t.pk)


# --------------------------
# Team Builder / CSV
# --------------------------
@login_required
@permission_required("mavtournaments.manage_teams", raise_exception=True)
def team_builder(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    return render(request, "mavtournaments/team_builder.html", _ctx_tournament(t))

@login_required
@permission_required("mavtournaments.manage_teams", raise_exception=True)
def bulk_teams(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    return render(request, "mavtournaments/bulk_teams.html", _ctx_tournament(t))

@login_required
@permission_required("mavtournaments.manage_teams", raise_exception=True)
def bulk_teams_preview(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    messages.error(request, "Nothing to preview yet (placeholder).")
    return redirect("tournaments:bulk_teams", pk=t.pk)

@login_required
@permission_required("mavtournaments.manage_teams", raise_exception=True)
def bulk_teams_confirm(request, pk):
    t = get_object_or_404(Tournament, pk=pk)
    messages.success(request, "No teams created (placeholder).")
    return redirect("tournaments:teams", pk=t.pk)

@login_required
def csv_template(request, pk):
    sample = "Team Alpha, alice, bob\nTeam Beta, carol, dave\n"
    resp = HttpResponse(sample, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename=\"mavbracket_csv_template_{pk}.csv\"'
    return resp
