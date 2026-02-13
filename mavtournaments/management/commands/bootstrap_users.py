# mavtournaments/management/commands/bootstrap_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from mavtournaments.models import Tournament, Team, TeamMembership

User = get_user_model()

SCOREKEEPER_GROUP = "Scorekeepers"
SCOREKEEPER_PERMS = [
    "manage_teams",       # create/edit teams
    "manage_seeding",     # generate bracket
    "advance_match",      # set winner
]

class Command(BaseCommand):
    help = "Create test users, Scorekeepers group with perms, and optionally attach users to teams."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1) Create superuser
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True}
        )
        if created:
            admin.set_password("adminpass")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created superuser admin / adminpass"))
        else:
            self.stdout.write("Superuser 'admin' already exists (password unchanged).")

        # 2) Scorekeepers group + perms
        group, _ = Group.objects.get_or_create(name=SCOREKEEPER_GROUP)
        added = []
        for codename in SCOREKEEPER_PERMS:
            try:
                perm = Permission.objects.get(codename=codename)
                group.permissions.add(perm)
                added.append(codename)
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Permission not found: {codename}"))
        if added:
            self.stdout.write(self.style.SUCCESS(f"Scorekeepers group updated with: {', '.join(added)}"))

        # 3) Scorekeeper user
        score1, created = User.objects.get_or_create(
            username="score1",
            defaults={"email": "score1@example.com", "is_staff": True}
        )
        if created:
            score1.set_password("scorepass")
            score1.save()
            self.stdout.write(self.style.SUCCESS("Created scorekeeper score1 / scorepass"))
        score1.groups.add(group)

        # 4) Basic users
        created_any = False
        for i in range(1, 11):
            uname = f"user{i}"
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={"email": f"{uname}@example.com", "first_name": f"User{i}", "last_name": "Demo"}
            )
            if created:
                u.set_password("password")
                u.save()
                created_any = True
        if created_any:
            self.stdout.write(self.style.SUCCESS("Created user1..user10 (password: password)"))
        else:
            self.stdout.write("user1..user10 already exist (passwords unchanged).")

        # 5) (Optional) attach a few users to teams in Demo Bracket if present
        try:
            t = Tournament.objects.get(name="Demo Bracket")
            teams = list(Team.objects.filter(tournament=t).order_by("name"))
            # put user1+user2 on first team, user3+user4 on second team (max 2 enforced)
            pairs = [("user1", "user2"), ("user3", "user4")]
            for pair, team in zip(pairs, teams[:2]):
                for uname in pair:
                    u = User.objects.get(username=uname)
                    TeamMembership.objects.get_or_create(team=team, user=u)
            self.stdout.write(self.style.SUCCESS("Attached user1..user4 to first two Demo teams."))
        except Tournament.DoesNotExist:
            self.stdout.write("Demo Bracket not found (skip team attachments).")
