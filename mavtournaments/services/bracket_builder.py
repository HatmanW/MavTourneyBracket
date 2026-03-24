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
        t.status = "DRAFT"
        t.save(update_fields=["status"])
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
    if winner is None or winner.id not in {match.team1_id, match.team2_id}:
        raise ValueError("Winner must be one of the teams in this match.")

    loser = match.team2 if match.team1_id == winner.id else match.team1
    match.winner = winner
    match.loser = loser
    match.save(update_fields=["winner", "loser"])

    # Don't count BYEs as real wins/losses
    if not match.is_bye:
        if winner:
            winner.wins += 1
            winner.save(update_fields=["wins"])
        if loser:
            loser.losses += 1
            loser.save(update_fields=["losses"])

    # Advance winner ONLY to the next match slot.
    # Do NOT auto-win the next round just because the other side isn't filled yet.
    if cascade and match.next_win:
        target = match.next_win
        updates = []

        # Deterministic placement:
        # even slot feeds team1, odd slot feeds team2
        if match.slot % 2 == 0:
            if target.team1_id != winner.id:
                target.team1 = winner
                updates.append("team1")
        else:
            if target.team2_id != winner.id:
                target.team2 = winner
                updates.append("team2")

        # If both sides are now filled, this is not a bye
        if target.team1_id and target.team2_id and target.is_bye:
            target.is_bye = False
            updates.append("is_bye")

        if updates:
            target.save(update_fields=updates)

    # finish flag if this was the final
    final = Match.objects.filter(tournament=match.tournament).order_by("-round__index", "slot").first()
    if final and final.id == match.id and match.winner:
        trn = match.tournament
        trn.status = "FINISHED"
        trn.save(update_fields=["status"])