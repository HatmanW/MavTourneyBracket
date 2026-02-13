# mavtournaments/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import Tournament, Team

User = get_user_model()

class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ["name", "elimination_type", "team_cap", "default_team_size"]

class TeamBuilderForm(forms.Form):
    name = forms.CharField(label="Team name", max_length=255)
    members = forms.ModelMultipleChoiceField(
        label="Members",
        queryset=User.objects.filter(is_active=True).order_by("username"),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 8, "class": "form-select"})
    )
    max_players = forms.IntegerField(label="Max players", min_value=1, max_value=64)

    def __init__(self, *args, **kwargs):
        default_max = kwargs.pop("default_max", 2)
        super().__init__(*args, **kwargs)
        self.fields["max_players"].initial = default_max

    def clean(self):
        cleaned = super().clean()
        members = cleaned.get("members") or []
        max_players = cleaned.get("max_players") or 2
        if len(members) > max_players:
            raise forms.ValidationError("You selected more members than the max players.")
        return cleaned

class BulkTeamsForm(forms.Form):
    """
    Users can either UPLOAD a CSV or PASTE lines.

    CSV/Paste accepted formats (no header required):
      Team Alpha, alice, bob
      Team Beta; carol,dave,eric
    """
    file = forms.FileField(label="Upload CSV file", required=False)
    raw = forms.CharField(
        label="Or paste teams",
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 8,
            "class": "form-control",
            "placeholder": "Team Alpha, alice, bob\nTeam Beta; carol,dave"
        })
    )
    default_max_players = forms.IntegerField(label="Max players per team", min_value=1, max_value=64)
    create_missing_users = forms.BooleanField(
        required=False, initial=False,
        help_text="If checked, unknown usernames will be auto-created with a random password."
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("file") and not cleaned.get("raw"):
            raise forms.ValidationError("Please upload a CSV file or paste team lines.")
        return cleaned

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form_control", "placeholder": "Team name"}),
        }