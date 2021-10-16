from django import forms

class CreateClanForm(forms.Form):
    clan_name = forms.CharField(max_length = 127, label='Create a clan:')

class InviteMemberForm(forms.Form):
    invitee = forms.CharField(max_length = 32, label='Invite:')
