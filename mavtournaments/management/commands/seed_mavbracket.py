#TourneyBracket/mavtournaments/management/commands/seed_mavbracket.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from mavtournaments.models import Tournament, Team, TeamMembership

User = get_user_model()

TEAM_NAMES = [
    "Beavers","Snakes","Falcons","Cyclones","Badgers","Dragons","Wolves","Marlins",
    "Panthers","Comets","Sharks","Ravens","Coyotes","Spartans","Mustangs","Knights",
    "Jets","Titans","Vikings","Pirates","Lions","Eagles","Tigers","Hawks",
    "Bulls","Raiders","Warriors","Pythons","Cobras","Rockets","Thunder","Storm"
]

FIRST = ["Alex","Taylor","Jordan","Sam","Casey","Riley","Jamie","Morgan","Devin","Quinn",
         "Avery","Cameron","Parker","Reese","Rowan","Skyler","Harper","Drew","Shawn","Kendall",
         "Chris","Pat","Robin","Dana","Shane","Jessie","Sasha","Marley","Elliot","Kris",
         "Brook","Logan","Blake","Shannon","Ari","Noel","Sage","Micah"]
LAST  = ["Smith","Johnson","Brown","Davis","Miller","Wilson","Moore","Taylor","Anderson","Thomas",
         "Jackson","White","Harris","Martin","Thompson","Garcia","Martinez","Robinson","Clark","Rodriguez",
         "Lewis","Lee","Walker","Hall","Allen","Young","Hernandez","King","Wright","Lopez",
         "Hill","Scott","Green","Adams","Baker","Gonzalez","Nelson","Carter","Mitchell","Perez"]

def make_name(i): return f"{FIRST[i%len(FIRST)]} {LAST[(i*3)%len(LAST)]}"

class Command(BaseCommand):
    help = "Seed demo tournament with 32 teams and players"

    @transaction.atomic
    def handle(self, *args, **opts):
        # users
        users = []
        for i in range(64):  # make 64 users
            username = f"player{i+1}"
            u, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": FIRST[i%len(FIRST)], "last_name": LAST[(i*3)%len(LAST)]}
            )
            if not u.email:
                u.email = f"{username}@example.com"; u.set_password("password"); u.save()
            users.append(u)

        # tournament
        t, _ = Tournament.objects.get_or_create(name="Demo Bracket", defaults={"team_cap": 32})
        # teams
        Team.objects.filter(tournament=t).delete()
        for i, team_name in enumerate(TEAM_NAMES):
            team = Team.objects.create(tournament=t, name=team_name)
            a, b = users[2*i], users[2*i+1]
            TeamMembership.objects.get_or_create(team=team, user=a)
            TeamMembership.objects.get_or_create(team=team, user=b)
        self.stdout.write(self.style.SUCCESS("Seeded Demo Bracket with 32 teams"))
