from django import forms
from django.contrib.auth.models import Group

from .models import PikiPage


class EditForm(forms.ModelForm):
    class Meta:
        model = PikiPage
        fields = [
            "page_txt",
            "tags",
            "owner", "owner_perms_read", "owner_perms_write",
            "group", "group_perms_read", "group_perms_write",
            "other_perms_read", "other_perms_write",]


class GroupForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False)


class PermForm(forms.Form):
    owner_perms_read = forms.BooleanField(initial=True, required=False, label="Read (owner)")
    owner_perms_write = forms.BooleanField(initial=True, required=False, label="Write (owner)")
    group_perms_read = forms.BooleanField(initial=True, required=False, label="Read (group)")
    group_perms_write = forms.BooleanField(initial=True, required=False, label="Write (group)")
    other_perms_read = forms.BooleanField(initial=True, required=False, label="Read (other)")
    other_perms_write = forms.BooleanField(initial=False, required=False, label="Write (other)")


class RenameForm(forms.Form):  # Note that it is not inheriting from forms.ModelForm
    page_name = forms.CharField(max_length=500, label="Change the page name:", required=True)

    def __init__(self, *args, **kwargs) -> None:
        page_name = kwargs.pop("page_name")
        super().__init__(*args, **kwargs)
        self.fields['page_name'].initial = page_name
