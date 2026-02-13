# mavtournaments/models.py
from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Tournament(models.Model):
    SINGLE = "SINGLE"
    ELIM_CHOICES = [(SINGLE, "Single Elimination")]

    name = models.CharField(max_length=255)
    elimination_type = models.CharField(max_length=12, choices=ELIM_CHOICES, default=SINGLE)
    team_cap = models.PositiveIntegerField(default=32)
    # NEW: per-tournament default team size (2 or 4 etc)
    default_team_size = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(
        max_length=16,
        choices=[("DRAFT", "Draft"), ("ACTIVE", "Active"), ("FINISHED", "Finished")],
        default="DRAFT",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Team(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=255)

    # Team can be >2 members now; forms default to tournament.default_team_size
    max_players = models.PositiveSmallIntegerField(default=2)

    # Legacy text fields kept for quick entry / display fallbacks
    participant1 = models.CharField(max_length=120, blank=True, default="")
    participant2 = models.CharField(max_length=120, blank=True, default="")

    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)

    # search index
    search_slug = models.CharField(max_length=300, editable=False, default="")

    # Proper user membership (you already had TeamMembership; we keep/define it below)
    players = models.ManyToManyField(User, through="TeamMembership", related_name="teams")

    class Meta:
        unique_together = ("tournament", "name")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.search_slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    @property
    def player_count(self) -> int:
        return self.players.count()

    def has_capacity(self) -> bool:
        return self.player_count < self.max_players

    def can_add(self, n: int = 1) -> bool:
        return (self.player_count + n) <= self.max_players

    @property
    def participants_display(self) -> str:
        parts = [p for p in [self.participant1, self.participant2] if p]
        return " & ".join(parts) if parts else "—"


class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="membership")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=20, default="player")  # future: captain/coach etc.

    class Meta:
        unique_together = ("team", "user")

    def __str__(self) -> str:
        return f"{self.user} → {self.team} ({self.role})"


class Round(models.Model):
    WINNERS = "WINNERS"

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="rounds")
    bracket = models.CharField(max_length=12, default=WINNERS)
    index = models.PositiveIntegerField(help_text="0-based round index")

    class Meta:
        unique_together = ("tournament", "bracket", "index")
        ordering = ["index"]

    def __str__(self) -> str:
        return f"R{self.index + 1}"


class Match(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="matches")
    slot = models.PositiveIntegerField(help_text="0-based position within the round")

    team1 = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="as_team1")
    team2 = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="as_team2")
    winner = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="as_winner")
    loser = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name="as_loser")

    # For winner advancement
    next_win = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="from_prev")

    is_bye = models.BooleanField(default=False)

    class Meta:
        unique_together = ("round", "slot")
        ordering = ["round__index", "slot"]

    def label(self) -> str:
        return f"R{self.round.index + 1}-M{self.slot + 1}"
