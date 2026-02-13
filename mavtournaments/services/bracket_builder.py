#mavtournaments/services/bracket_builder.py
import math
import random
from typing import List
from django.db import transaction
from mavtournaments.models import Tournament, Round, Match, Team

def _next_power_of_two(n: int) -> int:
    return 1 << (n - 1).bit_length()

@transaction.atomic
def generate_single_elim(t: Tournament, seed_method: str = "POWER"):
    # wipe existing
    Match.objects.filter(tournament=t).delete()
    Round.objects.filter(tournament=t).delete()

    teams: List[Team] = list(t.teams.all())
    n = len(teams)
    if n < 2:
        return

    M = _next_power_of_two(n)          # bracket size (power of two)
    rounds = int(math.log2(M))

    # rounds
    r_objs = [Round.objects.create(tournament=t, index=i) for i in range(rounds)]

    # seeding
    if seed_method == "RANDOM":
        random.shuffle(teams)
        first_pairs = []
        for i in range(M // 2):
            t1 = teams[2*i] if 2*i < n else None
            t2 = teams[2*i+1] if 2*i+1 < n else None
            first_pairs.append((t1, t2))
    else:
        # POWER: 1 vs M, 2 vs M-1, ...
        seeds = list(range(1, M + 1))
        pairs = [(s, M + 1 - s) for s in range(1, M // 2 + 1)]
        slots = {seed: (teams[seed - 1] if seed <= n else None) for seed in seeds}
        first_pairs = [(slots[a], slots[b]) for (a, b) in pairs]

    # create first round matches
    prev_round_matches = []
    for i, (t1, t2) in enumerate(first_pairs):
        is_bye = (t1 is None) ^ (t2 is None)
        m = Match.objects.create(
            tournament=t, round=r_objs[0], slot=i, team1=t1, team2=t2, is_bye=is_bye
        )
        prev_round_matches.append(m)

    # create remaining rounds and wire next_win pointers
    for ri in range(1, rounds):
        current = []
        for i in range(len(prev_round_matches) // 2):
            m = Match.objects.create(tournament=t, round=r_objs[ri], slot=i)
            a = prev_round_matches[2*i]
            b = prev_round_matches[2*i+1]
            a.next_win = m; a.save(update_fields=["next_win"])
            b.next_win = m; b.save(update_fields=["next_win"])
            current.append(m)
        prev_round_matches = current

    # resolve byes automatically
    for m in Match.objects.filter(tournament=t, round__index=0, is_bye=True):
        auto = m.team1 or m.team2
        if auto:
            set_winner(m, auto, cascade=True)

    t.status = "ACTIVE"
    t.save(update_fields=["status"])

def set_winner(match: Match, winner: Team, cascade: bool = True):
    loser = match.team2 if match.team1 == winner else match.team1
    match.winner = winner
    match.loser = loser
    match.save(update_fields=["winner", "loser"])

    if winner:
        winner.wins += 1; winner.save(update_fields=["wins"])
    if loser:
        loser.losses += 1; loser.save(update_fields=["losses"])

    # advance
    if cascade and match.next_win:
        target = match.next_win
        if target.team1 is None:
            target.team1 = winner
        elif target.team2 is None:
            target.team2 = winner
        target.save(update_fields=["team1","team2"])

        # propagate unexpected byes mid-tree
        if (target.team1 is None) ^ (target.team2 is None):
            target.is_bye = True
            target.save(update_fields=["is_bye"])
            auto = target.team1 or target.team2
            if auto:
                set_winner(target, auto, cascade=True)

    # finish flag if this was the final
    final = Match.objects.filter(tournament=match.tournament).order_by("-round__index","slot").first()
    if final and final.id == match.id and match.winner:
        trn = match.tournament
        trn.status = "FINISHED"
        trn.save(update_fields=["status"])
