from django import forms
import unicodedata

class CreateClanForm(forms.Form):
    clan_name = forms.CharField(max_length = 127, label='Create a clan:')

    # Custom validator for the clan_name field. Enforces some constraints we
    # don't want to allow in clan names.
    def clean_clan_name(self):
        data = self.cleaned_data['clan_name']

        # refuse slashes, since this will mess up routing to /clan/<clanname>
        # endpoints
        # (post 2021 TODO: we could probably improve this by making the clan name
        # a GET parameter rather than part of the URL)
        if '/' in data:
            raise forms.ValidationError('Clan names cannot contain slashes')

        # allow diacritics, but only one combining character per regular character
        # (otherwise ZALGO style clan names can be created which mess up other
        # parts of the page)
        prevcombine = False
        for char in data:
            nowcombine = unicodedata.combining(char)
            if nowcombine and prevcombine:
                raise forms.ValidationError('Clan names cannot have more than two consecutive combining characters')
            prevcombine = nowcombine

        return self.cleaned_data['clan_name']

class InviteMemberForm(forms.Form):
    invitee = forms.CharField(max_length = 32, label='Invite:')
