from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.conf import settings

# Registration form
class UserRegisterForm(UserCreationForm):
    #made toggleable in the settings.py to turn email requiement to true or false.
    email = forms.EmailField(required=settings.REQUIRE_EMAIL_FOR_REGISTRATION)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# User update form
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']


# Profile update form
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image', 'phone_number', 'first_name', 'last_name', 'bio']
